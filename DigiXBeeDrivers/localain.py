############################################################################
#                                                                          #
#                              Class LocalAIN                              #
#                                                                          #
############################################################################
#                                                                          #
# This class derives from the base XBeeDevice class, and implements        #
# the Analog IO layer of the Digi ConnectPort X device family.             #
# The local XBee module is used to read the analog inputs.                 #
#                                                                          #
############################################################################
#                                                                          #
# Functions:                                                               #
#                                                                          #
#    configure(channel, mode) - Define channel usage                       #
#        channel - Channel number to be configured.                        #
#        mode    - One of (CurrentLoop, TenV)                              #
#                                                                          #
#    raw_sample(channel)                                                   #
#        channel - Channel number to be read.                              #
#        Returns raw analog sample data for specified channel              #
#                                                                          #
#    sample(channel)                                                       #
#        channel - Channel number to be read.                              #
#        Returns sensor data scaled appropriately for operating mode       #
#                                                                          #
############################################################################

import xbee
import digihw
import time
from xbeedevice import *
from sensor_io import parseIS

Analog = 1

Unknown = 0
CurrentLoop = 1
TenV = 2

loopR = 51.25
tenVscale = 3.3 / 28.2

calInterval = 300
calTime = -calInterval
scale = 1
offset = 0

debug = False

# commands to configure XBee inputs
input_lines = [ "d0", "d1", "d2", "d3" ]


class LocalAIN(XBeeDevice):
    """LocalAIN - object representing the local analog input device.

This object allows the configuration and use of an XBee Analog device.
The XBee analog can operate each channel in one of two modes.

1. Ten volt.
2. 4-20mA current loop

Selection of the operating mode determines the scaling of the internal
analog to digital conversion.  The unit defaults to ten volt mode.  Be
careful when selecting a mode to choose appropriately to avoid damage
to the device.
"""
    def __init__(self):
        XBeeDevice.__init__(self, None)

        self.channels = [ Unknown, Unknown, Unknown, Unknown ]
        
    def configure(self, channel, mode):
        """configure(channel, mode) - Define channel usage

		channel - Channel number to be configured.
		mode    - One of (CurrentLoop, TenV)
		"""
        if channel >= len(input_lines):
            raise ValueError, "Unrecognized channel"

        if digihw.get_channel_type(channel) != Analog:
            raise ValueError, "Not an analog input channel"

        if mode == CurrentLoop or mode == TenV:
            digihw.configure_channel(channel, mode)
            self.XBeeCommandSet(input_lines[channel], 2)
        else:
            raise ValueError, "Unrecognized mode"

        self.channels[channel] = mode

    def calibrate(self):
        """calibrate()
        Calibrate analog inputs. Calculates scale and offset."""

	global calTime, scale, offset
	calTime = time.clock()
	
        # XBee series 1 uses one calibration voltage on AN2
        if self.device_type == XBeeSeries1:
        
	    if digihw.get_channel_type(1) != Analog:
		raise ValueError, "No analog input channels"
		
	    # Configure channel 1 as analog input
            self.XBeeCommandSet(input_lines[1], 2)

	    # Enable calibration voltage on channel 1
	    self.XBeeCommandSet("d4", 4)
	    time.sleep(0.010)

	    # Read calibration sample
	    result = self.XBeeCommandGet("is")
	    sample = parseIS(result)["AI1"]
	    
	    if debug:
	    	print "calibration sample is %d" % sample

	    # Return channel to operating mode
	    self.XBeeCommandSet("d4", 5)
	    time.sleep(0.010)

	    if sample == 0:
		raise ValueError, "Calibration error: bad sample"

	    # Calulate linear scale and offset.
	    # These apply to all analog channels.
	    scale = 1.25 / sample
	    offset = 0

        # XBee series 2 uses two calibration voltages on AN1 and AN2
        elif self.device_type == XBeeSeries2 or self.device_type == XBeeZB:
        
	    if digihw.get_channel_type(0) != Analog or digihw.get_channel_type(1) != Analog:
		raise ValueError, "No analog input channels"

	    # Configure channels 0 and 1 as analog inputs
            self.XBeeCommandSet(input_lines[0], 2)
            self.XBeeCommandSet(input_lines[1], 2)

	    # Enable calibration voltages on channels 0 and 1
	    self.XBeeCommandSet("p2", 4)
	    self.XBeeCommandSet("d4", 4)
	    time.sleep(0.010)

	    # Read calibration samples
	    result = self.XBeeCommandGet("is")
	    data = parseIS(result)
	    sample = [ data["AI0"], data["AI1"] ]
	    
	    if debug:
                print "calibration samples are %d, %d" % (sample[0], sample[1])

	    # Return channels to operating mode
	    self.XBeeCommandSet("p2", 5)
	    self.XBeeCommandSet("d4", 5)
	    time.sleep(0.010)

	    if sample[0] == sample[1]:
		raise ValueError, "Calibration error: equal samples"
            
            scale1 = 511.5 / float(sample[1])
            scale2 = 853.333 / float(sample[0])
            scale = (scale1 + scale2) / 2.0

            # Wasn't sure how to figure this out...
            offset = 0
       
        else:
            raise ValueError, "XBee does not support analog inputs"
            
	if debug:
            print "scale is %f, offset is %f" % (scale, offset)

    def raw_sample(self, channel):
        """raw_sample(channel) => A/D reading
        Returns raw unscaled A/D convertor sample data"""

        if channel >= len(input_lines):
            raise ValueError, "Unrecognized channel"

        if digihw.get_channel_type(channel) != Analog:
            raise ValueError, "Not an analog input channel"

	# Calibrate every calInterval seconds
	now = time.clock()
	if debug:
	    print "time is %f, calTime is %f" % (now, calTime)
	if now >= calTime + calInterval or now < calTime:
	    self.calibrate()

        result = self.XBeeCommandGet("is")

        val = float(parseIS(result)["AI%d" % channel])
        val = scale * val
        val1 = int(round(val))
        return val1

    def sample(self, channel, sample = ""):
        """sample(channel) => Reading in mA or V

        Returns sensor data scaled appropriately for operating mode"""
	
        if not sample:
            sample = self.raw_sample(channel)

	if debug:
	    print "sample is %d" % sample

        if self.channels[channel] == CurrentLoop:
            mV = float(sample) * 1200.0 / 1023.0
            mI = mV / loopR
            return mI
        elif self.channels[channel] == TenV:
            V = sample * 1.2 / 1023 / tenVscale
            return V
        else:
            raise ValueError, "Channel %d is not configured" % channel
