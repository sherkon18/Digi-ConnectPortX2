import socket
import struct
HOST = '170.168.8.221'
PORT = 20000
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
    print ("Failed to create TCP Connection")
    sys.exit()

print("Socket created")

try:
    client_socket.connect((HOST,PORT))
except socket.gaierror:
    print("Hostname count not be found, exiting...")
    sys.exit()
print("Connected to the server...")
while True:
        data = client_socket.recv(1024)
        lqi = ord(data[5000])
        print("lqi is: " + repr(lqi))
        RSSI = struct.unpack('b', data[28])[0]
        print("RSSI is: " + repr(RSSI))
