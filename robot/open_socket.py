from machine import Pin
import network
import socket
import time
from time import sleep
import irAndMotorsV3

PORT = 65535

def open_socket_connection():
    # Open network socket.
    s = socket.socket()
    s.bind(('', PORT))

    print("opened socket")
    # Listen for connections.
    led = Pin('LED', Pin.OUT)
    led.value(True)
    s.listen()
    while True:
        try:
            # Connect and send help text.
            print("trying to accept connection")
            conn, addr = s.accept()
            print('A client connected from', addr)
            # Process commands.
            while True:
                #data = conn.readline()
                data = conn.recv(1024)
                # print(line)
                print(data)
                data = eval(data)
                print(data)
                for x in data:
                    print(x)
                   
                    if x == 3:
                        irAndMotorsV3.drive()
                        
                            
                #if not line or line == b'\r\n':
                #   break
           
            
                conn.sendall(str(data))
                break
                        
        except OSError as e:
            conn.close()
            print('Connection closed')