
import socket
import select
import struct
import xbee
import errno
import table

###################################################################################################
# declarations 
###################################################################################################

MAX_TCP_PACKET_SIZE = 8192  #Maximum size of tcp packet we will receive or push at once
MAX_ZIG_PACKET_SIZE = 100   #Maximum size of zigbee packet we will read or send at once

tcp_port = 20000            #TCP Port the application sends and receives on 
quit_port = 30000           #TCP Port if connected to throws a keyboard exception

end_point  = 0x00           #address information that we will bind and send to
profile_id = 0x0000
cluster_id = 0x00

zig_addr_name_dict = table.table  #The dictionary of zigbee 64 bit hardware address mapped to names
                                  #This could be generated or typed in by the user

zig_queue = []                    #queue of data we send out the zigbee socket
tcp_queue = []                    #queue of data we send out the TCP socket


###################################################################################################
# cleanUp - removes the client socket from the read/write lists, closes and sets to None
###################################################################################################

def cleanUp(client_sock):  
  try:
    read_list.remove(client_sock)
    write_list.remove(client_sock)
    client_sock.close()
    client_sock = None
  except Exception, e:
    print e

###################################################################################################
# Detect radio type on the gateway
###################################################################################################

# This function detects the hardware version and uses that as a basis to determine what
# Addressing information we should use.

# In this case, anything over 6400 we determine as a Znet 2.5, anything before that
# as 802.15.4.

try:
  hw_version = xbee.ddo_get_param(None, "HV")
  hw_version = struct.unpack("=H", hw_version)[0]
except Exception, e:
  hw_version = None
  print e
  print "Failed to retrieve hardware version from local radio"
  print "Assuming it's a series 1 device"
  
if hw_version != None:
  if hw_version > 6400: #If the hardware version is greater then 6400, it must be a series 2 radio
    print "Detected Series 2 radio in gateway, configuring zigbee socket appropriately"
    end_point  = 0xE8 #232
    profile_id = 0xC105
    cluster_id = 0x11 #Out the UART
    MAX_ZIG_PACKET_SIZE = 72   #Packet sizes are at maximum 72 bytes
    
  else:
    print "Detected Series 1 radio in gateway, configuring zigbee socket appropriately"

###################################################################################################
# Init the dictionary, declare the sockets
###################################################################################################

# We provide reversal lookup to this dictionary. So we can go from the name -> 64 bit addr or
# 64 bit addr -> name.
 
for item in zig_addr_name_dict.keys():
  zig_addr_name_dict[zig_addr_name_dict[item]] = item
  #Reversal lookup now available!

# Declare the sockets
listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_sock.bind(("", tcp_port))
listen_sock.listen(1)

zig_sock = socket.socket(socket.AF_ZIGBEE, socket.SOCK_DGRAM, socket.ZBS_PROT_TRANSPORT)
zig_sock.bind(('', end_point, profile_id, cluster_id))
zig_sock.setblocking(0)

quit_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
quit_sock.bind(("", quit_port))
quit_sock.listen(1)

client_sock = None

read_list = [listen_sock, zig_sock, quit_sock]
write_list = [zig_sock]

###################################################################################################
# parser
###################################################################################################
def parseIS(data):

    ## We need to differentiate between series 1 and series 2 formats
    ## The series 1 format should always return a 'odd' byte count eg 7, 9, 11 or 13 bytes
    ## The series 2 format should always return a 'even' byte count eg, 8, 10, 12 or 14 bytes
    ## So we mod 2 the length, 0 is series 2, 1 is series 1.  Simple right?

    if len(data) % 2 == 0:
        sets, datamask, analogmask = struct.unpack("!BHB", data[:4])
        data = data[4:]

    else:
        sets, mask = struct.unpack("!BH", data[:3])
        data = data[3:]
        datamask = mask % 512 # Move the first 9 bits into a seperate mask
        analogmask  = mask >> 9 #Move the last 7 bits into a seperate mask

    retdir = {}

    if datamask:
        datavals = struct.unpack("!H", data[:2])[0]
        data = data[2:]

        currentDI = 0
        while datamask:
            if datamask & 1:
                retdir["DIO%d" % currentDI] = datavals & 1
            datamask >>= 1
            datavals >>= 1
            currentDI += 1

    currentAI = 0
    while analogmask:
        if analogmask & 1:
            aval = struct.unpack("!H", data[:2])[0]
            data = data[2:]

            retdir["AI%d" % currentAI] = aval
        analogmask >>= 1
        currentAI += 1

    return retdir

###################################################################################################
# Main loop
###################################################################################################

print "Entering main loop"

while 1:
  
  rl, wl, el = select.select(read_list, write_list, [])
  
  ###################################################################################################
  # Zigbee present in read list, we have new data
  ###################################################################################################
  
  if zig_sock in rl:
    try:
      data, addr = zig_sock.recvfrom(MAX_ZIG_PACKET_SIZE)
      print "Read %d bytes from address: %s" %(len(data), addr)
      parsedData = parseIS(data)
      print parsedData
    except Exception, e:
      print e
    else:
      try:
        name = zig_addr_name_dict[addr[0]] ## Get the name from the dictionary
      except KeyError, e:                  ## If that address doesn't have a name
        print e                            ## print and go no further here
      else:
        tcp_queue.append("%s:%s" %(name, parsedData)) ## Append the 'name:data' format to the queue
  
  ###################################################################################################
  # Zigbee present in write list AND we have data to write
  ###################################################################################################
  
  if (zig_sock in wl) and (len(zig_queue) != 0):    
    name, data = zig_queue[0].split(":", 1)    ## Retrieve the 'name:data' datoms
    name = name.strip()                        ## Strip excess unprintable characters
    try:
      addr = zig_addr_name_dict[name]          ## Get the addr dervied from the name
    except KeyError, e:
      #An node with an undefined address->Name mapping has contacted us
      print e
      
    else:
      if len(data) > MAX_ZIG_PACKET_SIZE:     
        segment = len(data)
      else:
        segment = MAX_ZIG_PACKET_SIZE
      
      try: 
        sent_data = zig_sock.sendto(data[:segment], 0, (addr, end_point, profile_id, cluster_id))
        data = data[sent_data:]
        if len(data) == 0:                     ## If all data has been sent, pop it
          zig_queue.pop(0)
        else:                                  ## Otherwise store the remaining data
          zig_queue[0] = "%s:%s" %(name, data)
      except Exception, e:
        print e
          
  ###################################################################################################
  # listening socket in read list, means we have a client!
  ###################################################################################################
  
  if listen_sock in rl:
    client_sock, addr = listen_sock.accept()
    client_sock.settimeout(0)                 ## disable blocking
    tcp_queue = []                            ## Remove all current data in queues
    zig_queue = []
    read_list.append(client_sock)             ## put the socket into a list so the select will cover     
    write_list.append(client_sock)            ## it when we next get back there.
    
  ###################################################################################################
  # client socket in read list, we have data
  ###################################################################################################
  
  if client_sock in rl:
    
    try:
      data = client_sock.recv(MAX_TCP_PACKET_SIZE)
      
    except socket.error, e:           #We have a socket exception
      if (e.args[0] == errno.EAGAIN): #If it's a blocking related exception
        pass                          #come back again next select call
      else:                           #If it's NOT a block related exception
        print e                       #Clean it up
        cleanUp(client_sock)           
    except Exception, e:
      print e
      cleanUp(client_sock)
    else:
      print "Read %s bytes from client" %len(data)
      if len(data) == 0:              ## If 0 bytes read, we clean up the connection 
        cleanUp(client_sock)
      
      pack =  data.split(":", 1)      ## split it by the first ':'
      if len(pack) != 2:              ## If the split item doesn't have 2 parts
        tcp_queue.append("ERROR: Invalid format, must follow 'NAME:DATA' format")
      else:                           ## Send back a message saying they didn't follow the format
        name = pack[0].strip()
        tail = pack[1]
            
        ## If we don't have an address associated with the key
        ## Send back a mesage saying it's unknown
        
        ## or if the item does not have anything after the ':'
        ## send back a message saying you sent no data
        
        ## if passing the above, queue up the message
        
        if zig_addr_name_dict.has_key(name) == False:  
          tcp_queue.append("ERROR: %s is an unknown name" %name)
        elif len(tail) == 0:
          tcp_queue.append("ERROR: Cannot send messages of 0 bytes in length")
        else:    
          zig_queue.append(data)
    
  ###################################################################################################
  # client socket in write list AND we have data to write
  ###################################################################################################
  
  if (client_sock in wl) and (len(tcp_queue) != 0):
    name = tcp_queue[0].split(":", 1)[0]  ## Retrieve the name from the item
    data = tcp_queue[0]                   ## Make a copy of the complete item
    
    if len(data) > MAX_TCP_PACKET_SIZE:
      segment = len(data)
    else:
      segment = MAX_TCP_PACKET_SIZE
    
    try:
      sent_data = client_sock.send(data[:segment])
    except socket.error, e:           #We have a socket exception
      if (e.args[0] == errno.EAGAIN): #If it's a blocking related exception
        pass                          #come back again next select call
      else:                           #If it's NOT a block related exception
        print e                       #Clean it up
        cleanUp(client_sock)           
    except Exception, e:
      print e
      cleanUp(client_sock)
    else:
      data = data[sent_data:]         ## Make the copy shorter by the amount we sent
      
      if len(data) == 0:              ## If that's all the data, pop the item from the queue
        tcp_queue.pop(0)
      elif sent_data < len(name) + 1: ## If we only sent enough to cover the 'name:' portion
        pass                          ## Don't store the changes, we didn't do anything
      else:
        tcp_queue[0] = "%s:%s" %(name, data)  ## Otherwise store the remaining chunk.
  
  ###################################################################################################
  # quit socket - convience to quit from the app
  ###################################################################################################
  
  if quit_sock in rl:
    raise KeyboardInterrupt("Quitting the application")
  
