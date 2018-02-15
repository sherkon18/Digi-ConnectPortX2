import socket
import struct
import xlwt



def connect(addr):
    con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    con.connect(addr)
    print("connecting...")
    return con


addr = ('170.168.8.221', 20000)
client_socket = connect(addr)
print("client_socket connected ")
packet_size = 60
data = ""
while True:
        while len(data) < packet_size:
            d = client_socket.recv(1024)
            print("Data: "+ d)
            wb = xlwt.Workbook()
            ws = wb.add_sheet("Xbee Data",cell_overwrite_ok=True)
            ws.write(0,0,data)
            wb.save('xbeeData2.xls')




    #     if not d:
    #         client_socket.close()
    #         client_socket = connect(addr)
    #     else:
    #         data += d
    # packet, data, = data[:packet_size], data[packet_size:]
    # lqi = ord(packet[27])
    # print ("lqi is", repr(lqi))
    # RSSI = struct.unpack('b', data[28])[0]
    # print ("rssi is: ", repr(RSSI))