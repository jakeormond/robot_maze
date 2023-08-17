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
        line_distances1, line_distances2 = dr.turn_in_place(data[1], conn)
        
        print(line_distances1)
        print(line_distances2)
        
        conn.sendall(str(line_distances1))
        conn.sendall(str(line_distances2))
                
    elif data[0] == 97: # simply get ir sensor values 
        sensor_value1, sensor_value2 = dr.read_sensors()
        sensor_str = f"sensor value 1: {sensor_value1}, sensor value2: {sensor_value2}"
        conn.sendall(sensor_str)
            
    elif data[0] == 98: # run linear drive
        
        line_distances1, line_distances2, \
            gap_distances1, gap_distances2 = dr.linear_drive(data[1], conn)
        
        print(line_distances1)
        print(line_distances2)
        print(gap_distances1)
        print(gap_distances2)
        
        conn.sendall(str(line_distances1))
        conn.sendall(str(line_distances2))
        conn.sendall(str(gap_distances1))
        conn.sendall(str(gap_distances2))
    
    elif data[0] == 99:  # run honeycomb program
        for i, d in enumerate(data[1:]):
            if i%2 == 0:
                line_distances1, line_distances2 = \
                    dr.turn_in_place(d, conn)
                
                conn.sendall(str(line_distances1))
                conn.sendall(str(line_distances2))
            else:
                line_distances1, line_distances2, \
                    gap_distances1, gap_distances2 = dr.linear_drive(d, conn)
                        
                conn.sendall(str(line_distances1))
                conn.sendall(str(line_distances2))
                conn.sendall(str(gap_distances1))
                conn.sendall(str(gap_distances2))

    elif data[0] == 100:  # find_line(-direction)
        direction = data[1]
        found_flag = dr.find_line(direction, conn)
        conn.sendall('found line : ' + str(found_flag))
        
    elif data[0] == 101:  # drive_forward_by_distance(distance)
        distance = data[1]
        distance = dr.drive_forward_by_distance(distance)
        conn.sendall('distance forward : ' + str(distance))
    
    
    else:    # bad command
        conn.sendall('bad command')


