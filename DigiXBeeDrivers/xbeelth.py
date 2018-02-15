############################################################################
#                                                                          #
#                              Class XBeeLTHN                              #
#                                                                          #
############################################################################
#                                                                          #
# This class derives from the base XBeeDevice class, and implements        #
# the LTH (Light/Temperature/Humidity) layer of the Digi XBee LTH Adapter. #
#                                                                          #
############################################################################
#                                                                          #
# Functions:                                                               #
#                                                                          #
#    raw_sample()                                                          #
#                                                                          #
#        Returns a dictionary of raw analog sample data                    #
#                                                                          #
#        The dictionary will contain the following keys:                   #
#            1) 'temperature'                                              #
#            2) 'light'                                                    #
#            3) 'humidity'                                                 #
#                                                                          #
#                                                                          #
#    sample()                                                              #
#                                                                          #
#        Returns a dictionary of data scaled into actual usable values.    #
#                                                                          #
#        The dictionary will contain the following keys:                   #
#            1) 'temperature' - Degrees in Celcius.                        #
#            2) 'light' - value in lux.                                    #
#            3) 'humidity' - value in %rh                                  #
#                                                                          #
############################################################################

import zigbee
from xbeeprodid import *
from xbeedevice import *
from sensor_io import parseIS

class XBeeLTHN(XBeeDevice):
    """XBeeLTHN - object representing a an XBee LTH device on the mesh.
    This object allows the configuration and use of an XBee LTH device."""
    
    def __init__(self, addr):
        """init(addr) addr - IEEE 802.15.4 address of XBee LTH Adapter module."""
        XBeeDevice.__init__(self, addr)
        # Verify that device is truly a LTH Adapter
        if self.product_type != XBeeSensorLTHAdapter:
            raise ValueError, "Adapter is not a %s" % (GetXBeeProductName(XBeeSensorLTHAdapter))

        # The XBee needs to have analog IO 1, 2, and 3 (pins 19, 18, 17) set to 'ADC'
        self.XBeeCommandSet("d1", 2)
        self.XBeeCommandSet("d2", 2)
        self.XBeeCommandSet("d3", 2)
        self.XBeeCommandSet("wr", "")
        self.XBeeCommandSet("ac", "")

    def raw_sample(self, io_sample=None):
        """raw_sample(channel) => A/D reading
        Returns raw unscaled A/D light, temperature and humidity sample data"""
        
        if io_sample is None:
            io_sample = self.XBeeCommandGet("is")
                    
        light = parseIS(io_sample)["AI1"]
        temp  = parseIS(io_sample)["AI2"]
        hum   = parseIS(io_sample)["AI3"]

        item = {'temperature': temp, 'light': light, 'humidity': hum}
        return item

    def sample(self, io_sample=None):
        """sample() => Converts raw sensor data into actual usable values."""

        item = self.raw_sample(io_sample)
        mVanalog = (float(item['temperature'])  / 1023.0) * 1200.0
        temp_C = (mVanalog - 500.0)/ 10.0 # -4.0
        ##NOTE:  Removed self heating correction of -4.0 celsius. 
        ##       Device is intended to be battery powered, which produces minimal 
        ##       self heating.  - MK 3/04/09

        lux = (float(item['light'])  / 1023.0) * 1200.0

        mVanalog = (float(item['humidity']) / 1023.0) * 1200.0
        hum = (((mVanalog * 108.2 / 33.2) / 5000 - 0.16) / 0.0062)

        item = { 'temperature': temp_C, 'light': lux, 'humidity': hum }
        return item
