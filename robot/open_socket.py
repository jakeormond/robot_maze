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

    led = Pin('LED', Pin.OUT)
    led.value(False)
    
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', PORT))

    print("opened socket")
    # Listen for connections.
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
                
            if not data:
                print(f' >> {addr} disconnected')
                break
            
            print(f"Received  {data}")
            parse_data(data, conn)                
                    
        except OSError as e:
            print(f' >> ERROR: {e}')
            
        finally:
            print('Connection closed')      
            conn.close()
    
    s.close()   
    
            
def parse_data(data, conn):
    # print(data)
    data = [int(s) for s in data.decode().split(',')]
    # print(data)
    
    if data[0] == 96: # turn in place
        # print(f"data is {data[1]}")
        n_lines = data[1]
        line_distances1, line_distances2 = dr.turn_in_place(data[1], data[2], conn)
        
        print(line_distances1)
        print(line_distances2)
        
        conn.sendall(str(line_distances1))
        conn.sendall(str(line_distances2))
                
    elif data[0] == 97: # simply get ir sensor values 
        sensor_value1, sensor_value2 = dr.read_sensors()
        sensor_str = f"sensor value 1: {sensor_value1}, sensor value2: {sensor_value2}"
        conn.sendall(sensor_str)
        
    elif data[0] == 98: # run turning test program
        encoder_distance1, encoder_distance2 = dr.turn_test()
        conn.sendall(str([encoder_distance1, encoder_distance2]))

    elif data[0] == 99: # run linear test program
        encoder_distance1, encoder_distance2 = dr.get_linear_distance()
        conn.sendall(str([encoder_distance1, encoder_distance2]))
               
    elif data[0] == 100: # send multiple messages
        conn.sendall('message 1,')
        sleep(.1)
        conn.sendall('message 2,')
        sleep(.1)
        conn.sendall('message 3,')
        
    elif data[0] == 101: # send multiple messages
        return_zero = dr.drive_straight_for_time(5, 5, 5)
        conn.sendall(str(return_zero) + ',')
        conn.sendall('done,')

    else:    # bad command
        conn.sendall('bad command')


