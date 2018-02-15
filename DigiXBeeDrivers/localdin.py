############################################################################
#                                                                          #
#                              Class LocalDIN                              #
#                                                                          #
############################################################################
#                                                                          #
# This class derives from the base XBeeDevice class, and implements        #
# the Digital IO layer of the Digi ConnectPort X device family.            #
# The local XBee module is used to read the digital inputs.                #
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
############################################################################

import xbee
import digihw
from xbeedevice import *
from sensor_io import parseIS

# Control lines for configuration
control_lines = [ "d0", "d1", "d2", "d3" ]

Digital = 2

Input = 0
Output = 1

Mode_Input = 3
Mode_OutputLow = 4

class LocalDIN(XBeeDevice):
    """ XBeeDIN - object representing a an XBee Digital device on the mesh.

"""
    def __init__(self):
        """init(addr)

addr - IEEE 802.15.4 address of XBee Analog module.
"""
	XBeeDevice.__init__(self, None)

    def configure(self, channel, mode, highlow = 0):
        """ configure(channel, mode, highlow) - Define channel usage

channel - Channel number to be configured.
mode    - One of (Input, Output)
highlow - If in Output mode, this specifies whether the signal should be
          driven high or low.
"""
        if channel >= len(control_lines):
            raise ValueError, "Unrecognized channel"

        if digihw.get_channel_type(channel) != Digital:
            raise ValueError, "Not a digital channel"

	# XBee pin is always a digital input
	self.XBeeCommandSet(control_lines[channel], 3)
	
        if mode == Output and highlow == 0:
            digihw.configure_channel(channel, Mode_OutputLow)
        else:
            digihw.configure_channel(channel, Mode_Input)
        
    def sample(self, channel):
        """sample(channel)
        Returns digital sample data for specified channel"""

        if channel >= len(control_lines):
            raise ValueError, "Unrecognized channel"

        if digihw.get_channel_type(channel) != Digital:
            raise ValueError, "Not a digital channel"

        result = self.XBeeCommandGet("is")
        
        return parseIS(result)["DIO%d" % channel]
