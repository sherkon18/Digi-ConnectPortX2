import xbee, struct

def get_xbee_info():  
  dd = get_dd_value()
  
  dd_bind =   {0x10000:("", 0, 0, 0),
               0x20000:("", 0xe8, 0xc105, 0x11),
               0x30000:("", 0xe8, 0xc105, 0x11),
               0x40000:("", 0xe8, 0xc105, 0x11),
               0x50000:("", 0xe8, 0xc105, 0x11),
               0x60000:("", 0, 0, 0),
               0x70000:("", 0, 0, 0)}

  dd_packet = {0x10000:100,
               0x20000:72,
               0x30000:84,
               0x40000:238,
               0x50000:73,
               0x60000:256,
               0x70000:100}
  
  ee = get_ee_value()
  
  bind_args = dd_bind[dd]
  p_size    = dd_packet[dd]
    
  if ee == 1:
    p_size -= 18
  
  return bind_args, p_size

def get_ee_value():
  ee_raw = xbee.ddo_get_param(None, 'EE')
  ee_val = struct.unpack('=B', ee_raw)[0]
  return ee_val

def get_dd_value():
  dd_raw = xbee.ddo_get_param(None, 'DD')
  dd_raw = struct.unpack('=I', dd_raw)[0]
  dd = dd_raw & 0xF0000
  return dd

if __name__ == '__main__':
  print get_xbee_info()
