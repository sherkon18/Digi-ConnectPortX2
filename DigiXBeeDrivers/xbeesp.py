############################################################################
#                                                                          #
#                              Class XBeeSPN                               #
#                                                                          #
############################################################################
#                                                                          #
# This class creates an interface for the common uses of the XBee Smart    # 
# Plug class It derives from XBeeDevice class and implements three sensor  #
# functions, temperature, current and light. In addition it provides an    #
# interface to turn on/off the power relay.                                #
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
#            3) 'current'                                                  #
#                                                                          #
#                                                                          #
#    sample()                                                              #
#                                                                          #
#        Returns a dictionary of data scaled into actual usable values.    #
#                                                                          #
#        The dictionary will contain the following keys:                   #
#            1) 'temperature' - Degrees in Celcius.                        #
#            2) 'light' - value in lux.                                    #
#            3) 'current' - value in Amps.                                 #
#                                                                          #
#                                                                          #
#                                                                          #
#    power(state)                                                          #
#                                                                          #
#        Sets the state of the power relay on the device                   #
#                                                                          #
#        To turn the power relay on, input 'True'                          #
#        To turn the power relay off, input 'False'                        #
#                                                                          #
############################################################################

import zigbee
from xbeeprodid import *
from xbeedevice import *
from sensor_io import parseIS

class XBeeSPN(XBeeDevice):
  """ XBeeSPN - object representing a XBee Smart Plug Adapter that is
      available on the mesh.  This object creates particial configuration,
      sampling, and power relay management.
      
      When created, 5 commands are executed:
        D1 = 2
        D2 = 2
        D3 = 2
        AC = None
        WR = None
      
      This sets the 3 dio lines for analog sampling and applies the changes
      and writes to flash.
      
      If these commands should fail a ValueError exception is raised.
  """
      
  
  def __init__(self, addr):
    """ This is used to initialize the object.  The 'addr' parameter
        represents the 64 bit hardware address of the node.  """
    
    XBeeDevice.__init__(self, addr)
    
    if self.product_type != XBeeSmartPlugAdapter:
        raise ValueError, "Adapter is not a %s"%(GetXBeeProductName(XBeeSmartPlugAdapter))
    
    if self.XBeeCommandSet("d1", 2) == 1:
        raise ValueError("Failed to set d1 = 2 on the adapter!")
    if self.XBeeCommandSet("d2", 2) == 1:
        raise ValueError("Failed to set d2 = 2 on the adapter!")    
    if self.XBeeCommandSet("d3", 2) == 1:
        raise ValueError("Failed to set d3 = 2 on the adapter!")
    if self.XBeeCommandSet("ac", "") == 1:
        raise ValueError("Failed to apply changes to the adapter!")
    if self.XBeeCommandSet("wr", "") == 1:
        raise ValueError("Failed to write to flash on the adapter!")
        
  def raw_sample(self, io_sample=None):
    """  Provides a untransulated sample in dictionary form.    
         temperature, light, current."""
         
    if io_sample is None:         
        io_sample = self.XBeeCommandGet("is")    
        
    parsed_struct = parseIS(io_sample)
    return {'temperature': parsed_struct["AI2"], 'light': parsed_struct["AI1"], 
            'current': parsed_struct["AI3"]}
  
  def sample(self, io_sample=None):
    """ Provides a transulated sample in dictionary form.    
        temperature measured in celsius,
        light measured in lux,
        current measured in amps.
        Makes use of raw_sample to provide initial data."""
        
    item = self.raw_sample(io_sample)
    
    mV = (float(item["temperature"]) / 1023.0) * 1200.0
    temp_C = (mV - 500.0) /10.0 - 4.0
        
    lux = (float(item["light"]) / 1023.0) * 1200.0
    
    mV = (float(item["current"]) /1023.0) * 1200.0 
    current = (mV*(156.0/47.0) - 520.0) /180.0 * .7071
    
    return {'temperature': temp_C, "light": lux, "current": current}
  
  def power(self, state):
    """  Provides an interface to the power relay on the smart plug.
         Takes one parameter - 'state'. 'state' is True or False. True
         turns on the power relay, False turns off the power relay.  """
         
    if state:
      self.XBeeCommandSet('d4', 5)
    else:
      self.XBeeCommandSet('d4', 4)
            
    self.XBeeCommandSet("ac", "")
    self.XBeeCommandSet("wr", "")
      
