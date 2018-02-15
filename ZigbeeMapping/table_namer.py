import xbee

node_list = []
count = 1
output_file = "table.py"

for i in xrange(0, 5):
  
  new_nodes = xbee.getnodelist()  
  for node in new_nodes:
    found = False
    for old_node in node_list:
      if node.addr_extended == old_node.addr_extended:
        found = True
        break
    
    if not found:
      node_list.append(node)                       
    

fh = open("WEB/python/%s" %output_file, 'w')
fh.write("table = {\r\n")

for node in node_list:
  if node == node_list[-1]:    
    if node.label.strip() != "":
      fh.write("\t \"%s\": \"%s\"\r\n" %(node.addr_extended, node.label))      
    else:
      fh.write("\t \"%s\": \"%s\"\r\n" %(node.addr_extended, "Node_%d"%count))
      count+=1
  else:
    if node.label.strip() != "":
      fh.write("\t \"%s\": \"%s\",\r\n" %(node.addr_extended, node.label))      
    else:
      fh.write("\t \"%s\": \"%s\",\r\n" %(node.addr_extended, "Node_%d"%count))
      count+=1    

fh.write("}\r\n")
fh.close()

print "wrote %d entries" %len(node_list)
