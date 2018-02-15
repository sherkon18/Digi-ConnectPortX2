############################################################################
#                                                                          #
#                              Class XBeeAIN                               #
#                                                                          #
############################################################################
#                                                                          #
# This class derives from the base XBeeDevice class, and implements        #
# the Analog IO layer of the Digi XBee Analog IO Adapter.                  #
#                                                                          #
############################################################################
#                                                                          #
# Functions:                                                               #
#                                                                          #
#    configure(channel, mode) - Define channel usage                       #
#        channel - Channel number to be configured.                        #
#        mode    - One of (CurrentLoop, TenV, Differential)                #
#                                                                          #
#    raw_sample(channel)                                                   #
#        channel - Channel number to be read.                              #
#        Returns raw analog sample data for specified channel              #
#                                                                          #
#    sample(channel)                                                       #
#        channel - Channel number to be read.                              #
#        Returns sensor data scaled appropriately for operating mode       #
#                                                                          #
#    power(onoff) - Toggles Power Output on Terminal 6.                    #
#        onoff - Specifies Power Output either on (1) or off (0).          #
#                                                                          #
############################################################################

import zigbee
from xbeeprodid import *
from xbeedevice import *
from sensor_io import parseIS

Unknown = 0
CurrentLoop = 1
TenV = 2
Differential = 3

DifferentialMidPointChannel0 = 490
DifferentialMidPointChannel2 = 490
DifferentialMax = 2.54
DifferentialMin = -2.352

loopR = 51.1
tenVscale = 3.3 / 28.2

# Control lines for configuration
#                   out   sw
ain_control_lines = [ ["d4", "d8"],
                      ["d6", "d8"],
                      ["d7", "p0"],
                      ["p2", "p0"],
                    ]

out = 0
sw = 1

# commands to configure XBee inputs
ain_input_lines = [ "d0", "d1", "d2", "d3" ]

class XBeeAIN(XBeeDevice):
    """XBeeAIN - object representing a an XBee Analog device on the mesh.
    This object allows the configuration and use of an XBee Analog device.
    The XBee analog can operate each channel in one of three modes.

    1. Ten volt.
    2. 4-20mA current loop
    3. +/- 2V Differential

    Selection of the operating mode determines the scaling of the internal
    analog to digital conversion.  The unit defaults to ten volt mode and
    that is also the mode that the paired channel for differential
    operation will be returned to when differential mode is exited.  Be
    careful when selecting a mode to choose appropriately to avoid damage
    to the device.
    """
    
    def __init__(self, addr):
        """ addr - IEEE 802.15.4 address of XBee Analog module.
        Examples: '[00:13:a2:00:40:0a:12:90]!' """
        
        XBeeDevice.__init__(self, addr)
        # Verify that device is truly a Analog IO Adapter
        
        if self.product_type != XBeeAnalogIOAdapter:
            raise ValueError("Adapter is not a %s" % (GetXBeeProductName(XBeeAnalogIOAdapter)))

        self.channels = [ Unknown, Unknown, Unknown, Unknown ]

    def configure(self, channel, mode):
        """configure(channel, mode) - Define channel usage

        channel - Channel number to be configured.
        mode    - One of (CurrentLoop, TenV, Differential)

        Differential mode is only configurable for even numbered channels.
        However, the channels are paired so that when differential mode is
        configured, the paired channel will also change modes.  When exiting
        differential mode, the paired channel will be placed into ten volt
        measurement mode and require reconfiguration if current loop operation
        is desired.
        """
        
        assert channel < len(ain_control_lines), "Unrecognized channel"
        assert channel >= 0, "Unrecognized channel"        

        # Verify combinations of configuration make sense
        if channel % 2 == 1:
          
            assert mode != Differential, "Differential can only be set on even channels"            
            assert self.channels[channel - 1] != Differential, \
                "Cannot change mode, paired channel is configured for Differential operation"                                  
                
        if mode == CurrentLoop:
            self.XBeeCommandSet(ain_control_lines[channel][out], 4)
            self.XBeeCommandSet(ain_control_lines[channel][sw], 4)
        elif mode == TenV:
            self.XBeeCommandSet(ain_control_lines[channel][out], 5)
            self.XBeeCommandSet(ain_control_lines[channel][sw], 4)
        elif mode == Differential:
            self.XBeeCommandSet(ain_control_lines[channel][out], 4)
            self.XBeeCommandSet(ain_control_lines[channel][sw], 5)
            self.XBeeCommandSet(ain_control_lines[channel+1][out], 4)
        else:
            raise ValueError, "Unrecognized mode"

        if self.channels[channel] == Differential and mode != Differential:
            self.XBeeCommandSet(ain_control_lines[channel + 1][out], 5)
            self.channels[channel + 1] = TenV
        
        self.channels[channel] = mode

        if mode == Differential:
            self.channels[channel + 1] = Differential

        self.XBeeCommandSet(ain_input_lines[channel], 2)
        self.XBeeCommandSet("ac", "")
        self.XBeeCommandSet("wr", "")

    def raw_sample(self, channel, io_sample=None):
        """raw_sample(channel) => A/D reading
        Returns raw unscaled A/D converter sample data"""
        if channel >= len(ain_control_lines):
            raise ValueError, "Unrecognized channel"

        if io_sample is None:
            io_sample = self.XBeeCommandGet("is")

        return parseIS(io_sample)["AI%d" % channel]

    def sample(self, channel, io_sample=None):
        """sample(channel) => Reading in mA or V

        Returns sensor data scaled appropriately for operating mode"""

        sample = self.raw_sample(channel, io_sample)

        if self.channels[channel] == CurrentLoop:
            mV = sample * 1200.0 / 1023
            mI = mV / loopR
            return mI

        elif self.channels[channel] == TenV:
            V = sample * 1.2 / 1023 / tenVscale
            return V

        elif self.channels[channel] == Differential:
            if channel == 0:
                mid = DifferentialMidPointChannel0
            else:
                mid = DifferentialMidPointChannel2
            if sample >= mid:
                V = ((float(sample) - float(mid)) / (1023.0 - float(mid))) * DifferentialMax
            else:
                V = ((float(mid) - float(sample)) / float(mid)) * DifferentialMin
            return V

        else:
            raise ValueError, "Channel %d is not configured" % channel
 
    def power(self, state):
        """power(onoff)
        Toggles power output on Terminal 6"""

        if state:
            self.XBeeCommandSet("p3", 5)
        else:
            self.XBeeCommandSet("p3", 4)

        self.XBeeCommandSet("ac", "")
        self.XBeeCommandSet("wr", "")
