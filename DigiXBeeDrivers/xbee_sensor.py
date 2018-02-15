# ****************************************************************************
# Copyright (c) 2007 Digi International Inc., All Rights Reserved
# 
# This software contains proprietary and confidential information of Digi
# International Inc.  By accepting transfer of this copy, Recipient agrees
# to retain this software in confidence, to prevent disclosure to others,
# and to make no use of this software other than that for which it was
# delivered.  This is an unpublished copyrighted work of Digi International
# Inc.  Except as permitted by federal law, 17 USC 117, copying is strictly
# prohibited.
# 
# Restricted Rights Legend
#
# Use, duplication, or disclosure by the Government is subject to
# restrictions set forth in sub-paragraph (c)(1)(ii) of The Rights in
# Technical Data and Computer Software clause at DFARS 252.227-7031 or
# subparagraphs (c)(1) and (2) of the Commercial Computer Software -
# Restricted Rights at 48 CFR 52.227-19, as applicable.
#
# Digi International Inc. 11001 Bren Road East, Minnetonka, MN 55343
#
# ***************************************************************************

#
# Support for XBee Sensors
#

import math
import struct

class XBeeSensor:
    def __init__(self):
	pass

    class _1SSample:
	AD_VDD     = 5.1  # Supply voltage to the A/D converter
	AD_BITMASK = 0xff # Bit mask for the A/D (here, 8-bits)

	def __init__(self, sample):
	    # Intialize our attributes:
	    self.sample = []
	    self.sensors = 0
	    self.ad_sample = [None] * 4
	    self.temperature = None

	    # Do the parsing:
	    self.sample = struct.unpack("!B4HH", sample)
	    self.sensors = self.sample[0]

	    ad_to_v = lambda ad: (ad / float(self.AD_BITMASK)) * self.AD_VDD

	    if self.has_ad():
		self.ad_sample = []
		self.ad_sample.append(ad_to_v(self.sample[1]))
		self.ad_sample.append(ad_to_v(self.sample[2]))
		self.ad_sample.append(ad_to_v(self.sample[3]))
		self.ad_sample.append(ad_to_v(self.sample[4]))

            if self.has_temperature():
                temp = struct.pack('>h', ~self.sample[5])
                self.temperature = ~struct.unpack('>h', temp)[0] / 16.0

	def __repr__(self):
	    str = "<_1SSample"
	    if self.has_temperature():
		str += " Temp: y (%f)" % (self.temperature)
	    else:
		str += " Temp: n"
	    if self.has_ad():
		str += " A/D: y (%s)" % (self.ad_sample)
	    else:
		str += " A/D: n"
	    str += ">"
	    return str

	def has_ad(self):
	    if self.sensors & 0x01:
		return True
	    return False
	
	def has_temperature(self):
	    if self.sensors & 0x02:
		return True
	    return False

	def ad_sample_to_v(self, ad_sample):
	    return (ad_sample / float(self.AD_BITMASK)) * self.AD_VDD

    def parse_sample(self, sample):
	return self._1SSample(sample)

class XBeeWatchportA(XBeeSensor):
    V_DD = 5.00
    SENSITIVITY = 0.312

    def __init__(self):
	# Initialize our attributes:
	self.xout = 0
	self.yout = 0
	self.pitch = 0
	self.roll = 0

	# Initialize private variables:
	self._calibration_xout = 0
	self._calibration_yout = 0

	XBeeSensor.__init__(self)

    def __repr__(self):
	return "<XBeeWatchportA xout=%f yout=%f pitch=%f roll=%f>" % \
		(self.xout, self.yout, self.pitch, self.roll)

    def set_0g_calibration(self, sample):
	calibration = self.parse_sample(sample, False)
	self._calibration_xout = -calibration.xout
	self._calibration_yout = -calibration.yout
	self.xout = 0
	self.yout = 0
	self.pitch = 0
	self.roll = 0

    def parse_sample(self, sample):
	sample_obj = XBeeSensor.parse_sample(self, sample)

	if not sample_obj.has_ad():
	    raise ValueError, "Given sample has no A/D values."

	v_to_g = lambda v: (v - (self.V_DD / 2)) / self.SENSITIVITY
	self.xout = ( v_to_g(sample_obj.ad_sample[3]) +
			self._calibration_xout )
	self.yout = ( v_to_g(sample_obj.ad_sample[2]) +
			self._calibration_yout )
      
	# Function to clip a value x between -1 <= x <= 1:
	clip = lambda x: [[x, -1][x < -1], 1][x > 1]

	# Calculate pitch and roll:
	self.pitch = math.degrees(math.asin(clip(self.xout)))
	self.roll = math.degrees(math.asin(clip(self.yout)))

	return self

class XBeeWatchportD(XBeeSensor):
    def __init__(self):
	# Initialize our attributes:
	self.distance = 0

	XBeeSensor.__init__(self)

    def __repr__(self):
	return "<XBeeWatchportD distance=%f>" % (self.distance)

    def parse_sample(self, sample):
	sample_obj = XBeeSensor.parse_sample(self, sample)

	# Calculate distance:
	v = sample_obj.ad_sample[3]
	if v <= 0.43:
	    self.distance = 150
	elif v >= 2.5:
	    self.distance = 20
	else:
	    # This function was derived from performing a regression
	    # on observed data, it is only an approximation:
	    self.distance = 61.442 * math.pow(v, -1.073)

	return self

class XBeeWatchportH(XBeeSensor):
    def __init__(self):
	# Initialize our attributes:
	self.sensor_rh = 0
	self.true_rh = 0
	self.temperature = 0

	XBeeSensor.__init__(self)

    def __repr__(self):
	return "<XBeeWatchportH sensor_rh=%f true_rh=%f temperature=%f>" % \
		    (self.sensor_rh, self.true_rh, self.temperature)

    def parse_sample(self, sample):
	sample_obj = XBeeSensor.parse_sample(self, sample)

	v_supply = sample_obj.ad_sample[2]
	v_output = sample_obj.ad_sample[3]

	# These equations are given by the HIH-3610 series datasheet:
	self.sensor_rh = (1 / 0.0062) * ((v_output / v_supply) - 0.16)
	self.true_rh = self.sensor_rh / (1.0546 - (0.00216 * sample_obj.temperature))
	self.temperature = sample_obj.temperature

	return self

class XBeeWatchportT(XBeeSensor):
    def  __init__(self):
	self.temperature = 0

	XBeeSensor.__init__(self)

    def __repr__(self):
	return "<XBeeWatchportT temperature=%f>" % (self.temperature)

    def parse_sample(self, sample):
	sample_obj = XBeeSensor.parse_sample(self, sample)
	self.temperature = sample_obj.temperature
	return self

class XBeeWatchportW:
  def __init__(self):
    self.water = False
  
  def __repr__(self):
    return "<XBeeWatchportW Water present=%s>"%(self.water)
  
  def parse_sample(self, sample):
    if ord(sample[0]) & 128:
      self.water = True
    else:
      self.water = False
    return self
