############################################################################
#                                                                          #
#                              Class XBeeLTN                               #
#                                                                          #
############################################################################
#                                                                          #
# This class derives from the base XBeeDevice class, and implements        #
# the LT (Light/Temperature) layer of the Digi XBee LT Adapter.            #
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
#                                                                          #
#                                                                          #
#    sample()                                                              #
#                                                                          #
#        Returns a dictionary of data scaled into actual usable values.    #
#                                                                          #
#        The dictionary will contain the following keys:                   #
#            1) 'temperature' - Degrees in Celcius.                        #
#            2) 'light' - value in lux.                                    #
#                                                                          #
############################################################################

import zigbee
from xbeeprodid import *
from xbeedevice import *
from sensor_io import parseIS

class XBeeLTN(XBeeDevice):
    """XBeeLTN - object representing a an XBee LT device on the mesh.
    This object allows the configuration and use of an XBee LT device."""
    
    def __init__(self, addr):
        """addr - IEEE 802.15.4 address of XBee LT Adapter module."""
        
        XBeeDevice.__init__(self, addr)
        # Verify that device is truly a LT Adapter
        if self.product_type != XBeeSensorLTAdapter:
            raise ValueError, "Adapter is not a %s" % (GetXBeeProductName(XBeeSensorLTAdapter))

        # The XBee needs to have analog IO 1 and 2 (pins 19, 18) set to 'ADC'
        self.XBeeCommandSet("d1", 2)
        self.XBeeCommandSet("d2", 2)
        self.XBeeCommandSet("wr", "")
        self.XBeeCommandSet("ac", "")

    def raw_sample(self, io_sample=None):
        """raw_sample(channel) => A/D reading
        Returns raw unscaled A/D light and temperature sample data"""
        
        if io_sample is None:
          io_sample = self.XBeeCommandGet("is")
                
        light = parseIS(io_sample)["AI1"]
        temp  = parseIS(io_sample)["AI2"]

        item = {'temperature': temp, 'light': light}
        return item

    def sample(self, io_sample=None):
        """sample() => Converts raw sensor data into actual usable values."""

        item = self.raw_sample(io_sample)

        mVanalog = (float(item['temperature'])  / 1023.0) * 1200.0
        temp_C = (mVanalog - 500.0)/ 10.0 # - 4.0
        ##NOTE:  Removed self heating correction of -4.0 celsius. 
        ##       Device is intended to be battery powered, which produces minimal 
        ##       self heating.  - MK 3/04/09

        lux = (float(item['light'])  / 1023.0) * 1200.0

        item = { 'temperature': temp_C, 'light': lux }
        return item
