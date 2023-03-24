from machine import Pin
import network
import socket
import time
from time import sleep
# import irAndMotorsV3
import drive_robot as dr

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
            # while True:
            data = conn.recv(1024)
            parse_data(data, conn)
            
            conn.close()
            print('Connection closed')
            
                        
        except OSError as e:
            conn.close()
            print('Connection closed')
            
def parse_data(data, conn):
    data = [int(s) for s in data.decode().split(',')]
    
    if len(data) > 1: # drive the robot
        jake = 1
                
    elif data[0] == 97: # simply get ir sensor values 
        sensor_value1, sensor_value2 = dr.read_sensors()
        conn.sendall(str([sensor_value1, sensor_value2]))
        
    elif data[0] == 98: # run turning test program
        encoder_distance1, encoder_distance2 = dr.turn_test()
        conn.sendall(str([sensor_value1, sensor_value2]))

    elif data[0] == 99: # run linear test program
        encoder_distance1, encoder_distance2 = dr.get_linear_distance()
        conn.sendall(str([sensor_value1, sensor_value2]))

    else:    # bad command
        conn.sendall('bad command')


