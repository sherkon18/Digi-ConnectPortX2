
import socket

HOST = '170.168.9.61'          # The remote host
PORT = 5000               # The port as used by the server

def main():
    # Create the socket and connect to the remote server.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    
    # Send data to the server.
    s.send('Hello, world')
    
    # Receive data from the remote server and print it.
    data = s.recv(1024)
    print 'Received', repr(data)
    
    s.close()

if __name__ == '__main__':
    main()
