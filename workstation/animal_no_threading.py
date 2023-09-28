''' 
The animal class contains the animal's position calculated 
from the tracking data. It also contains the animal's choice.
'''
import socket
import os
import csv
import struct
import numpy as np
import threading
import time
import pickle

MIN_PLATFORM_TIME = 1 # length of time animal needs to be on 
# new platform before choice is registered

class Animal:
    def __init__(self, host, port, buffer_size, n):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.n = n
        self.data_buffer = []
        self.current_platform = None

    def get_next_platform(self, possible_platforms, start_platform,
                      platform_coordinates, crop_coordinates):
        
        while True:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
                udp_socket.bind((self.host, self.port))
                
                try:
                    data, _ = udp_socket.recvfrom(self.buffer_size)
                    parsed_data = self.parse_most_recent_data(data)

                    curr_plat = get_current_platform(parsed_data, possible_platforms, 
                            platform_coordinates, crop_coordinates)

                    timestamp = time.time()

                    # Process and store the received data
                    self.store_data((curr_plat, timestamp))

                    # find the next platform
                    recent_data = self.get_data()

                    target_platform = recent_data[-1][0]

                    if target_platform != start_platform:
                        recent_data = recent_data[::-1]
                        target_time = recent_data[0][1]
                        for i in range(1, len(recent_data)):
                            if recent_data[i][0] == target_platform:
                                start_time = recent_data[i][1]
                                duration = target_time - start_time

                                if duration >= MIN_PLATFORM_TIME:
                                    new_platform = target_platform
                                    self.current_platform = new_platform
                                    return new_platform
                            else:
                                break

                except socket.timeout:
                    # Handle socket timeout error here
                    print("Socket timeout error: Unable to receive data. Retrying...")
                    # You can add more specific error handling or retry logic here

                except Exception as e:
                    # Handle other exceptions here
                    print(f"Error: {e}")
                    # You can add more specific error handling or logging here

        
    def store_data(self, data):
        # Add the new data point to the buffer
        self.data_buffer.append(data)
        
        # Ensure the buffer does not exceed 'n' data points
        if len(self.data_buffer) > self.n:
            self.data_buffer.pop(0)  # Remove the oldest data point

    def get_data(self):
        return self.data_buffer
    
    def parse_most_recent_data(self, data):
        parsed_data = parse_data(data)
        return parsed_data  

    def get_current_platform(self):
        return self.current_platform
    
    
def parse_data(received_data):
    parsed_data = np.zeros((6))

    indices = [18, 22, 26, 30, 34, 38]

    for i, index in enumerate(indices):
        parsed_data[i] = int.from_bytes(received_data[index:index+2], byteorder='big', signed=True)
    
    return parsed_data

def get_current_platform(parsed_data, possible_platforms, 
                         platform_coordinates, crop_coordinates):
    # get the current position
    # remove any zero or negative values
    x_vals = parsed_data[::2]
    x_vals = x_vals[x_vals > 0]
    x_val = np.mean(x_vals) + crop_coordinates[0]

    y_vals = parsed_data[1::2]
    y_vals = y_vals[y_vals > 0]
    y_val = np.mean(y_vals) + crop_coordinates[1]

    # calculate distance to each platform
    distances = np.zeros((len(possible_platforms)))

    for i, platform in enumerate(possible_platforms):
        distances[i] = np.sqrt((x_val - platform_coordinates[platform][0])**2 + 
                               (y_val - platform_coordinates[platform][1])**2)

    if np.min(distances) > 100:
        current_platform = None
    
    else:
        # get the closest platform
        current_platform = possible_platforms[np.argmin(distances)]
    
    return current_platform

       
if __name__ == "__main__":
    
    # for testing
    # load platform_coordinates
    map_path = image_path = 'D:/testFolder/pico_robots/map'
    with open(map_path + '/platform_coordinates.pickle', 'rb') as handle:
        platform_coordinates = pickle.load(handle)

    # crop_coordinates
    crop_coor = (344, 204, 600, 600)  

    # possible_platforms
    possible_platforms = [61, 70, 71]  
    
    host = '0.0.0.0'  # server's IP address
    port = 8000  # UDP port
    buffer_size = 1024
    n = 200  # Number of previous data points to store

    receiver = Animal(host, port, buffer_size, n)

    current_platform = receiver.get_next_platform(possible_platforms, 61, platform_coordinates, crop_coor)

    print(current_platform)
    

  