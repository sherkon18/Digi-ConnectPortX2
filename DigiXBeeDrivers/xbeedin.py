############################################################################
#                                                                          #
#                              Class XBeeDIN                               #
#                                                                          #
############################################################################
#                                                                          #
# This class derives from the base XBeeDevice class, and implements        #
# the Digital IO layer of the Digi XBee Digital IO Adapter.                #
#                                                                          #
############################################################################
#                                                                          #
# Functions:                                                               #
#                                                                          #
#    configure(channel, mode, highlow) - Define channel usage              #
#        channel - Channel number to be configured.                        #
#        mode    - One of (Input, Output)                                  #
#        highlow - If in Output mode, this specifies whether the signal    #
#                  should be driven high (1) or low (0).                   #
#                                                                          #
#    sample(channel)                                                       #
#        channel - Channel number to be read.                              #
#        Returns digital sample data for specified channel                 #
#                                                                          #
#    power(onoff) - Toggles Power Output on Terminal 6.                    #
#        onoff - Specifies Power Output either on (1) or off (0).          #
#                                                                          #
############################################################################

import zigbee
from xbeedevice import *
from xbeeprodid import *
from sensor_io import parseIS

Unknown = 0

inp = 0
out = 1

# Control lines for configuration
#                   in    out
control_lines = [ ["d8", "d4"],
                  ["d1", "d6"],
                  ["d2", "d7"],
                  ["d3", "p2"],
                  ]

channel_to_pin = [ 8, 1, 2, 3 ]

Input = 0
Output = 1

class XBeeDIN(XBeeDevice):
    """ XBeeDIN - object representing a an XBee Digital device on the mesh."""
    
    def __init__(self, addr):
        """addr - IEEE 802.15.4 address of XBee Analog module."""
        
        XBeeDevice.__init__(self, addr)

        # Verify that device is truly a Digital IO Adapter
        if self.product_type != XBeeDigitalIOAdapter:
            raise ValueError("Adapter is not a %s" % (GetXBeeProductName(XBeeDigitalIOAdapter)))

        self.channels = [ Unknown, Unknown, Unknown, Unknown ]

    def configure(self, channel, mode, highlow = 0):
        """ configure(channel, mode, highlow) - Define channel usage
        channel - Channel number to be configured.
        mode    - One of (Input, Output)
        highlow - If in Output mode, this specifies whether the signal should be
        driven high or low.
        """
        
        assert channel < len(control_lines), "Unrecognized channel"
        assert channel >= 0, "Unrecognized channel"      

        if mode == Input:
            self.XBeeCommandSet(control_lines[channel][out], 4)
            self.XBeeCommandSet(control_lines[channel][inp], 3)
        else:
            if highlow == 1:
                self.XBeeCommandSet(control_lines[channel][out], 4)
            else:
                self.XBeeCommandSet(control_lines[channel][out], 5)

            self.XBeeCommandSet(control_lines[channel][inp], 4)
        
        self.channels[channel] = mode
        
        self.XBeeCommandSet("ac", "")
        self.XBeeCommandSet("wr", "")
        
    def sample(self, channel, io_sample=None):
        """sample(channel) Returns digital sample data for specified channel"""

        assert channel < len(control_lines), "Unrecognized channel"
        assert channel >= 0, "Unrecognized channel"     
        
        if io_sample is None:
            io_sample = self.XBeeCommandGet("is")            
        
	return parseIS(io_sample)["DIO%d" % channel_to_pin[channel]]

    def power(self, state):
        """power(state) Toggles power output on Terminal 6"""

        if state:
            self.XBeeCommandSet("p3", 5)
        else:
            self.XBeeCommandSet("p3", 4)

        self.XBeeCommandSet("ac", "")
        self.XBeeCommandSet("wr", "")
