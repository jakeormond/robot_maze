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

CHOICE_DURA = 1 # length of time animal needs to be on 
# new platform before choice is registered

class Animal:
    def __init__(self, host, port, buffer_size, n):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.n = n
        self.data_buffer = []
        self.data_receiver_thread = None
        self.terminate_thread = threading.Event()  # Termination flag for the data receiver thread

        # Start the data receiver thread when an instance is created
        # receiving a packet for every video frame, so roughly 30 per second
        # self.data_receiver_thread = threading.Thread(target=self.receive_data)
        # self.data_receiver_thread.start()

    def start_data_receiver(self, possible_platforms, platform_coordinates, 
                     crop_coordinates):
        # Start the data receiver thread
        if self.data_receiver_thread is None or not self.data_receiver_thread.is_alive():
            self.terminate_thread.clear()  # Clear the termination flag
            self.data_receiver_thread = threading.Thread(target=self.receive_data, 
                                            args=(possible_platforms, 
                                                    platform_coordinates, crop_coordinates))
            self.data_receiver_thread.start()

    def stop_data_receiver(self):
        # signal the thread to terminate
        self.terminate_thread.set()
        
        # Wait for the data receiver thread to finish
        if self.data_receiver_thread is not None and self.data_receiver_thread.is_alive():
            self.data_receiver_thread.join()  # Wait for the thread to finish
            self.data_receiver_thread = None  # Set it to None after stopping
            # clear the data buffer
            self.data_buffer = []

    def receive_data(self, possible_platforms, platform_coordinates, 
                     crop_coordinates):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.bind((self.host, self.port))
            while not self.terminate_thread.is_set():
                try:
                    data, _ = udp_socket.recvfrom(self.buffer_size)
                    parsed_data = self.parse_most_recent_data(data)

                    curr_plat = get_current_platform(parsed_data, possible_platforms, 
                         platform_coordinates, crop_coordinates)

                    timestamp = time.time()

                    # Process and store the received data
                    self.store_data((curr_plat, timestamp))
                except socket.timeout:
                    pass
        
    def store_data(self, data):
        # Add the new data point to the buffer
        self.data_buffer.append(data)
        
        # Ensure the buffer does not exceed 'n' data points
        if len(self.data_buffer) > self.n:
            self.data_buffer.pop(0)  # Remove the oldest data point

    def get_data(self):
        return self.data_buffer
    
    def find_next_platform(self, start_platform):
        while not self.terminate_thread.is_set():
            recent_data = self.get_data()

            if len(recent_data) > 0:
                # from the last data point, find the number of consecutive
                # data points with the same platform not equal to the 
                # start platform
                target_platform = recent_data[-1][0]

                if target_platform == start_platform:
                    continue
                
                # reverse recent data
                recent_data = recent_data[::-1]

                target_time = recent_data[0][1]
                counter = 0
                for i in range(len(recent_data)):
                    if recent_data[i][0] == target_platform:
                        counter += 1
                    else:
                        start_time = recent_data[i-1][1]
                        duration = target_time - start_time
                        if duration < CHOICE_DURA:
                            new_platform = None
                            continue

                        else:
                            new_platform = target_platform
                            break

            # Sleep for a while to avoid continuous processing
            time.sleep(.1)  # Adjust the sleep interval as needed
    
        return new_platform
    
    def start_next_platform_thread(self, start_platform):
        # Start a new thread to run the monitor_data_buffer method with the custom variable
        if self.data_receiver_thread is None or not self.data_receiver_thread.is_alive():
            self.terminate_thread.clear()
            self.platform_thread = threading.Thread(target=self.find_next_platform, args=(start_platform,))
            self.platform_thread.start()

    def stop_next_platform_thread(self):
        # Signal the monitor thread to terminate
        if hasattr(self, 'platform_thread'):
            self.terminate_thread.set()
            self.platform_thread.join()
 
   
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
    n = 100  # Number of previous data points to store

    receiver = Animal(host, port, buffer_size, n)

    # Now, you can access the recent data from the receiver object in your main program
    counter = 0
    while True:
        print(receiver.data_buffer)
        counter += 1

        if counter == 100:
            receiver.start_data_receiver(possible_platforms, platform_coordinates, 
                     crop_coor)
            print('Started data receiver thread')

        if counter == 200:
            receiver.stop_data_receiver()
            print('Stopped data receiver thread')

        if counter == 300:
            receiver.start_data_receiver(possible_platforms, platform_coordinates, 
                     crop_coor)
            print('Started data receiver thread')

        if counter == 400:
            receiver.stop_data_receiver()
            print('Stopped data receiver thread')

        # wait for .03 seconds
        time.sleep(.03)
       