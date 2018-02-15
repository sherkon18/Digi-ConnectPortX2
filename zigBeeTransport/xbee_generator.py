from xbee import getnodelist
import sys
import xbee_info

bind_args, packet_size = xbee_info.get_xbee_info() 

stored_nodes = []
port = 4000
discover_count = 3
output_file = 'bind_table.py'

print "Parsing args"
for i in xrange(1, len(sys.argv), 2):
  print "Parsing argument: ", sys.argv
  if sys.argv[i] == '-port':
    port = int(sys.argv[i+1])
  elif sys.argv[i] == '-discover':
    discover_count = int(sys.argv[i+1])
  elif sys.argv[i] == '-file':
    output_file = sys.argv[i+1]
  else:
    raise Exception("Unknown argument: %s" %sys.argv[i])

print "Performing discovery"
for i in xrange(0, discover_count):
  node_list = getnodelist()
  for node in node_list:
    for comp_node in stored_nodes:
      if node.addr_extended == comp_node[0]:
        break
    else:      
      node_entry = (node.addr_extended, bind_args[1], bind_args[2], bind_args[3])
      print "Storing node: ", node_entry
      stored_nodes.append(node_entry)

print "Writing out file"
fh = open('WEB/python/' + output_file, 'w')
fh.write('node_list = {\n')
for node in stored_nodes:
  if node == stored_nodes[-1]:
    fh.writelines('\t%s:%d\n' %(node, port))
  else:
    fh.writelines('\t%s:%d,\n' %(node, port))
  port += 1
fh.writelines('}')
fh.close()

print "Wrote %d entries" %len(stored_nodes)