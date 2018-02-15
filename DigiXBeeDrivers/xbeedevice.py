import zigbee
from xbeeprodid import *

amount_of_tries = 10

class XBeeDevice:
    """ XBeeDevice - An object representing any Digi XBee device on the mesh."""

    def __init__(self, addr):
        """init(addr) addr - IEEE 802.15.4 address of XBee Analog module. """

	device_type, product_type = GetXBeeDeviceType(addr)
	self.device_type = device_type
	self.product_type = product_type
        self.addr = addr

    def getname(self):
        """Gets official product name of device"""
        return GetXBeeProductName(self.product_type)

    def XBeeCommandSet(self, command, args):
        result = 1
        # Attempt the command a couple times if it fails for some reason.
        for i in range(0, amount_of_tries):
            try:
                zigbee.ddo_set_param(self.addr, command, args)                                    
            except:
                continue
            else:
                return 0
        print "XBeeCommandSet FAILED: %s %s" % (command, args)
        return 1

    def XBeeCommandGet(self, command):
        result = None
        # Attempt the command a couple times if it fails for some reason.
        for i in range(0, amount_of_tries):
            try:
		result = zigbee.ddo_get_param(self.addr, command)
            except:
                continue
            else:
                return result
        print "XBeeCommandGet FAILED: %s" % command
        return None

