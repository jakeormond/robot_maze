''' 
The animal class contains the animal's position calculated 
from the tracking data. It also contains the animal's choice.
'''
import socket
import numpy as np
import threading
import time
import pickle
import queue
import keyboard

MIN_PLATFORM_DURA = 10 # length of time animal needs to be on 
# new platform before choice is registered

class Animal:
    def __init__(self, host, port, buffer_size, n):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.n = n
        self.data_buffer = []
        self.current_platform = None
        self.data_receiver_thread = None
        self.manual_input_thread = None
        self.next_platform_event = threading.Event()  # Event to signal the next platform thread is finished       
        self.user_input_queue = queue.Queue()


    def find_new_platform(self, possible_platforms, start_platform, 
                            platform_coordinates, crop_coordinates):
        
        self._start_data_receiver(possible_platforms, start_platform, 
                            platform_coordinates, crop_coordinates)        
        
        self._start_manual_input_thread()
        self._wait_for_next_platform_event()       
        
    
    def _start_data_receiver(self, possible_platforms, start_platform, 
                            platform_coordinates, crop_coordinates):
        # Start the data receiver thread
        if self.data_receiver_thread is None or not self.data_receiver_thread.is_alive():
            self.data_receiver_thread = threading.Thread(target=self._receive_data, 
                                            args=(possible_platforms, start_platform,
                                                    platform_coordinates, crop_coordinates))
            self.data_receiver_thread.start()

    def _start_manual_input_thread(self):
        # Start the data receiver thread
        if self.manual_input_thread is None or not self.manual_input_thread.is_alive():
            self.manual_input_thread = threading.Thread(target=self.listen_for_key)
            self.manual_input_thread.start()


    def _wait_for_next_platform_event(self):
        # Block until the monitor event is set
        self.next_platform_event.wait()
                
        # Wait for the data receiver thread to finish
        if self.data_receiver_thread is not None and self.data_receiver_thread.is_alive():
            self.data_receiver_thread.join()  # Wait for the thread to finish
            self.data_receiver_thread = None  # Set it to None after stopping
        
        # finish the manual input thread
        if self.manual_input_thread is not None and self.manual_input_thread.is_alive():
            self.manual_input_thread.join()
            self.manual_input_thread = None
        
        # clear the data buffer
        self.data_buffer = []
        # clear the next platform event
        self.next_platform_event.clear()


    def _receive_data(self, possible_platforms, start_platform,
                      platform_coordinates, crop_coordinates):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.bind((self.host, self.port))
            
            while True: #not self.terminate_thread.is_set():
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

                                if duration >= MIN_PLATFORM_DURA:
                                    new_platform = target_platform
                                    self.current_platform = new_platform
                                    self.next_platform_event.set()
                                    return 
                            else:
                                break

                except socket.timeout:
                    # Handle socket timeout error here
                    print("Socket timeout error: Unable to receive data. Retrying...")
                    # You can add more specific error handling or retry logic heres

                except Exception as e:
                    # Handle other exceptions here
                    print(f"Error: {e}")
                    # You can add more specific error handling or logging here
    
    
    def listen_for_key(self):
        trigger_key = 's'

        while True:
            if receiver.next_platform_event.is_set():
                break

            if keyboard.is_pressed(trigger_key):
                # Execute the method when the trigger key is pressed
                self.execute_method()
                break
           
    def execute_method(self):
        print("Method executed!")
    
       
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

    receiver.find_new_platform(possible_platforms, 61, platform_coordinates, crop_coor)

    current_platform = receiver.get_current_platform()
    print(current_platform)
    print(current_platform)
    

  