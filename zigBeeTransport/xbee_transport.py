from socket import *
from select import *
from time import clock
from bind_table import node_list
import xbee_info
import sys

sys.path.append("WEB/python/xbee_transport.py")


bind_args, xb_psize = xbee_info.get_xbee_info()

sock_port   = {}
sock_client = {}
sock_queue  = {}
client_list = []
listen_list = []

def cleanup(client):
  client_list.remove(client)
  sock = sock_client[client]
  sock_client[sock] = None
  del sock_client[client]
  
  client.close()
  client = None 

def main():
  print "Creating lookup table"  
  dest_list = node_list.keys()
  for dest in dest_list:
    port = node_list[dest]
    node_list[port] = dest
    
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind(("", port)) 
    sock.settimeout(0)
    sock.listen(1)
    
    sock_port[sock] = port
    sock_port[port] = sock
    
    sock_client[sock] = None
    
    listen_list.append(sock)
  
  print "Creating xbee socket"
  print "Bind args are: ", bind_args
  print "Packet size is: ", xb_psize
  xb_sock = socket(AF_XBEE, SOCK_DGRAM, XBS_PROT_TRANSPORT)
  xb_sock.bind(bind_args)
  xb_sock.setsockopt(XBS_SOL_EP, XBS_SO_EP_SYNC_TX, 1)
  xb_sock.settimeout(0)
  
  TCP_BUFFERING_TIME = .300 #Time to buffer TCP packets, helps with zigbee fragmentation
                            #and may reduce TCP cost to send data
  
  quit_sock = socket(AF_INET, SOCK_STREAM)
  quit_sock.bind(('', 40001))
  quit_sock.listen(1)
  
  xb_queue = []

  print "Entering mainloop"
  while 1:
    read_list = [xb_sock] + listen_list + client_list + [quit_sock]
    write_list = [xb_sock] + client_list
    rl, wl, el = select(read_list, write_list, [], 1.0)
    
    if xb_sock in rl:
      data, addr = xb_sock.recvfrom(8192)
      print "Received %d bytes from address: " %len(data), addr      
      
      new_addr = (addr[0], addr[1], addr[2], addr[3])
      
      if node_list.has_key(new_addr):
        print "addr in node_list dict"
        port = node_list[new_addr]        
        sock = sock_port[port]        
        if sock_client[sock] is not None:
          print "Queueing data to be sent out TCP port"
          print "Clock time is: %f" %clock()
          if len(sock_queue[sock]) == 0:
            print "Queue is empty, appending data"
            sock_queue[sock].append((data, clock()))
          else:            
            packet_data, packet_time = sock_queue[sock][-1]
            if clock() - packet_time <= TCP_BUFFERING_TIME:
              print "Queue has item, meets TCP_BUFFERING_TIME condition, appending data to previous packet"              
              sock_queue[sock][-1] = (packet_data + data, packet_time)
            else:
              print "Queue has item, but is too old, not appending data to previous packet, appending to queue instead"
              sock_queue[sock].append((data, clock()))
            
          
    if xb_sock in wl and len(xb_queue) != 0:
      data, addr = xb_queue[0]
      send_size = (len(data) < xb_psize) and len(data) or xb_psize
      print "Writing %d bytes to dest: %s" %(send_size, str(dest))
      try:
        sent = xb_sock.sendto(data[:send_size], 0, addr)        
      except Exception, e:
        print "Exception occured sending to address: %s" %(str(addr))        
        xb_queue.pop(0)
        port = node_list[addr]
        sock = sock_port[port]
        if sock_client[sock] is not None:
          print "Sending error message to tcp client"
          sock_queue[sock].append(("ERROR: Destination %s could not be sent %s for reason: %s" %(addr, data, e), 0))
          
      else:      
        if sent == len(data):
          xb_queue.pop(0)
        else:
          xb_queue[0] = data[sent:], addr
    
    for sock in listen_list:
      if sock in rl:
        client, addr = sock.accept()
        print "Received TCP connection from address: ", addr
        sock_client[sock] = client
        sock_client[client] = sock
        
        sock_queue[sock]   = []        
        client_list.append(client)
    
    for client in client_list:
      if client in rl:
        print "Reading from client"
        try:
          data = client.recv(8192)
          print "Received %d bytes from TCP connection" %len(data)
        except Exception, e:
          print e
          cleanup(client)
          continue
        
        if len(data) == 0:
          cleanup(client)
          continue
        
        sock = sock_client[client]
        port = sock_port[sock]
        xb_queue.append((data, node_list[port]))
    
    for client in client_list:
      if client in wl:        
        sock = sock_client[client]
        if len(sock_queue[sock]) != 0:
          data, packet_time = sock_queue[sock][0]
          
          if clock() - packet_time >= TCP_BUFFERING_TIME:
            ##Data is ready to send
            print "Sending data, clock time is: %f" %clock()          
            try:
              sent = client.send(data)
              print "Wrote %d bytes out TCP connection" %sent
            except Exception, e:
              print e
              cleanup(client)
              continue
          
            if sent == len(data):
              sock_queue[sock].pop(0)
            else:
              sock_queue[sock][0] = (data[sent:], packet_time)
            
    if quit_sock in rl:
      raise KeyboardInterrupt("Stopping script, quit sock activated")
    
if __name__ == '__main__':
  main()