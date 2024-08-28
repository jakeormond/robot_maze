from machine import Pin
import machine
import network
import socket
import time
from time import sleep
import utime
# import irAndMotorsV3
import drive_robot as dr
import gc

led = Pin('LED', Pin.OUT)
led.value(False)

def connect(ipconfig, ssid, password):
    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.ifconfig(ipconfig)
    wlan.connect(ssid, password)
    wlan.PM_NONE

    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    led.value(True)
    return wlan

def open_socket_connection(PORT, wlan, ipconfig, ssid, password):
    # Open network socket.
    s = socket.socket()

    led = Pin('LED', Pin.OUT)
    led.value(False)
    
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', PORT))
    # s.setblocking(0)
    s.settimeout(2.0)

    print("opened socket")
    # Listen for connections.
    led.value(True)
    
    s.listen()
    time1 = time.time()
    while True:
        try:
            time2 = time.time()
            total_time = time2-time1
            print('total_time = ', total_time)
            
               
            if wlan.isconnected() == False:
                wlan.deinit()
                s.close()
                print('disconnected')
                return
                
            
            
            # if total_time > 40:
            #   wlan.deinit()
            #    s.close()
            #    print('disconnecting')
            #    if wlan.isconnected() == False:
            #        print('disconnected')
            #    else:
            #        print('disconnection didnt work')               
            #    
            #    return
                
                            
            print("trying to accept connection")
            conn, addr = s.accept()
            print('A client connected from', addr)
            # Process commands.
            # while True:
            gc.collect()
            
            data = conn.recv(1024)
                
            if not data:
                print(f' >> {addr} disconnected')
                break
            
            print(f"Received  {data}")
            time1 = time.time()
            return_flag = parse_data(data, conn)
            
            if return_flag == 0:
                send_data_flag = 0
                while send_data_flag == 0:
                    wlan.disconnect()
                    wlan = connect(ipconfig, ssid, password)
                    send_data_flag = send_data_only(PORT, wlan, ipconfig, ssid, password)               
       
                    
        except OSError as e:
            print(f' >> ERROR: {e}')
            
            if wlan.isconnected() == False:
                print('wifi was disconnected; rebooting')
                # wlan.disconnect()
                # s.close()
                machine.reset()
                # return
                
                # wlan = connect(ipconfig, ssid, password)
                
            else:
                print('wifi still connected')
                # wlan = connect(ipconfig, ssid, password)
            
        finally:
            
            if wlan.isconnected() == False:
                print('wifi was disconnected; reconnecting')
                wlan = connect(ipconfig, ssid, password)
    
    s.close()
    return
    # machine.reset()
    
def send_data_only(PORT, wlan, ipconfig, ssid, password):
    s = socket.socket()

    led = Pin('LED', Pin.OUT)
    led.value(False)
    
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', PORT))
    # s.setblocking(0)
    s.settimeout(2.0)

    print("opened socket")
    # Listen for connections.
    led.value(True)
    
    s.listen()
    time1 = time.time()
    
    while True:
        try:
            time2 = time.time()
            total_time = time2-time1
            print('total_time = ', total_time)
            
            if total_time > 10:
                wlan.disconnect()
                s.close()
                send_data_flag = 0
                # machine.reset()
                
                return send_data_flag
            
                       
            print("trying to accept connection")
            conn, addr = s.accept()
            print('A client connected from', addr)
            # Process commands.
            # while True:
            gc.collect()
            
            conn.sendall(str(0))
            send_data_flag = 1
            return send_data_flag
            
        except OSError as e:
            print(f' >> ERROR: {e}')
            send_data_flag = 0
            return send_data_flag     
            
def parse_data(data, conn):
    print('data = ', data)
    data = [int(s) for s in data.decode().split(',')]
    print(data)
    
    if data[0] == 96: 
        encoder_distance = dr.drive_forward_by_distance(data[1], conn)
         
        conn.sendall(str(encoder_distance))
        
    elif data[0] == 95: # simply get ir sensor values 
        found_flag = dr.find_line(data[1], conn)
       
        conn.sendall(str(found_flag) + ',')
        
    elif data[0] == 94: # simply get ir sensor values 
        dr.turn_by_distance(data[1], data[2], conn)
                
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
        print('running honeycomb program')
        for i, d in enumerate(data[1:]):
            if d == 0:
                # conn.sendall(str(0))
                pass
            
            if i%2 == 0:
                print('turning in place')
                line_distances1, line_distances2 = \
                    dr.turn_in_place(d, conn=conn)
                
                print(line_distances1)
                print(line_distances2)
                # conn.sendall(str(line_distances1))
                # conn.sendall(str(line_distances2))
            else:
                line_distances1, line_distances2, \
                    gap_distances1, gap_distances2 = dr.linear_drive(d, conn)
                        
                # conn.sendall(str(line_distances1))
                # conn.sendall(str(line_distances2))
                # conn.sendall(str(gap_distances1))
                # conn.sendall(str(gap_distances2))
        
        conn.settimeout(2.0)
        try:
            conn.sendall(str(0))
        except OSError as e:
            print(f' >> ERROR: {e}')
            return_flag = 0                    
            return
        
        gc.collect()
        
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
    
    # time.sleep(1)
    # machine.reset()
    conn.close()
    return_flag = 1
    return



