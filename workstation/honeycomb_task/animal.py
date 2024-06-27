''' 
The animal class handles the receiving of tracking data from Bonsai.
The find_new_platform method is called when new platforms are presented
to the animal, and will automatically determine the animal's choice.
If, for some reason, the animal's choice is not determined, the user
can manually select the animal's choice by pressing the 's' key, and 
then selecting from the 2 presented options.

In addition, there are some non-instance methods that are used to set 
the file names for Bonsai to save the data to, and also to provide Bonsai
with the crop parameters.
'''
import socket
import numpy as np
import threading
import time
import pickle
import keyboard
import os
import csv

MIN_PLATFORM_DURA = 2 # length of time animal needs to be on 
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


    def find_new_platform(self, possible_platforms, start_platform, 
                            platform_coordinates, crop_coordinates, min_platform_dura):
        
        # print("Finding new platform...")

        self._start_data_receiver(possible_platforms, start_platform, 
                            platform_coordinates, crop_coordinates, min_platform_dura)        
        
        self._start_manual_input_thread(possible_platforms, start_platform)
        self._wait_for_next_platform_event()    

        # unchosen platform is the platform that is neither the current platform
        # nor the start platform
        unchosen_platform = [x for x in possible_platforms if x != self.current_platform and x != start_platform][0]
        return self.current_platform, unchosen_platform 
        
    
    def _start_data_receiver(self, possible_platforms, start_platform, 
                            platform_coordinates, crop_coordinates, min_platform_dura):
        # Start the data receiver thread
        if self.data_receiver_thread is None or not self.data_receiver_thread.is_alive():
            self.data_receiver_thread = threading.Thread(target=self._receive_data, 
                                            args=(possible_platforms, start_platform,
                                                    platform_coordinates, crop_coordinates,
                                                    min_platform_dura))
            self.data_receiver_thread.start()

    def _start_manual_input_thread(self, possible_platforms, start_platform):
        # Start the data receiver thread
        if self.manual_input_thread is None or not self.manual_input_thread.is_alive():
            self.manual_input_thread = threading.Thread(target=self._listen_for_key, 
                                                        args=(possible_platforms, start_platform))
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
                      platform_coordinates, crop_coordinates, min_platform_dura):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.bind((self.host, self.port))
            
            while not self.next_platform_event.is_set(): #not self.terminate_thread.is_set():
                try:
                    data, _ = udp_socket.recvfrom(self.buffer_size)
                    parsed_data = self.parse_most_recent_data(data)

                    curr_plat = get_current_platform(parsed_data, possible_platforms, 
                         platform_coordinates, crop_coordinates)

                    timestamp = time.time()

                    # Process and store the received data
                    self._store_data((curr_plat, timestamp))

                    # find the next platform
                    recent_data = self.get_data()

                    target_platform = recent_data[-1][0]
                    
                    # just continue if we can't find the animal
                    if target_platform is None:
                        print('\nhaving difficulty finding the animal\npress s to manually register the choice')

                        continue

                    if target_platform != start_platform:
                        recent_data = recent_data[::-1]
                        target_time = recent_data[0][1]
                        for i in range(1, len(recent_data)):
                            if recent_data[i][0] == target_platform:
                                start_time = recent_data[i][1]
                                duration = target_time - start_time

                                if duration >= min_platform_dura:
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

                    time.sleep(0.01)  # Sleep for 100ms to prevent high CPU usage

                except Exception as e:
                    # Handle other exceptions here
                    print(f"Error: {e}")
                    # You can add more specific error handling or logging here
                
                    time.sleep(0.01)  # Sleep for 100ms to prevent high CPU usage

   
    def _listen_for_key(self, possible_platforms, start_platform):      
        trigger_key = 's'
        # Enter the blocking mode to suppress key events
        keyboard.block_key(trigger_key)

        while not self.next_platform_event.is_set():
            if keyboard.is_pressed(trigger_key):
                # Execute the method when the trigger key is pressed
                keyboard.unblock_key(trigger_key)
                self.next_platform_event.set()
                self._manually_select_platform(possible_platforms, start_platform)                
                return
            time.sleep(0.1)
        keyboard.unblock_key(trigger_key)

           
    def _manually_select_platform(self, possible_platforms, start_platform):
        # remove start_platform from possible_platforms
        # make a copy of possible_platforms
        choice_platforms = possible_platforms.copy()
        choice_platforms.remove(start_platform)
        print(f'\nStart platform is {start_platform}')
        print(f'\nPossible platforms are {choice_platforms[0]} and {choice_platforms[1]}')
        print("Manually select platform from the following options (press 1 or 2):")
        print(f"platforms 1: {choice_platforms[0]}, 2: {choice_platforms[1]}")
        while True:
            user_input = input("Enter your choice (1 or 2): ")
            
            if user_input == '1':
                self.current_platform = choice_platforms[0]
                return
            elif user_input == '2':
                self.current_platform = choice_platforms[1]
                return
            else:
                print("Invalid input. Please try again.")
                print(f"platforms 1: {choice_platforms[0]}, 2: {choice_platforms[1]}")
                    
       
    def _store_data(self, data):
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
    
    # sort the distances
    sorted_distances = np.sort(distances)
    # distance_diff is the difference between the closest and second closest platform
    distance_diff = sorted_distances[1] - sorted_distances[0]
    
    if np.min(distances) > 80 and distance_diff < 50: # was 100
        current_platform = None
    
    else:
        # get the closest platform
        current_platform = possible_platforms[np.argmin(distances)]
    
    return current_platform

def write_date_and_time(datetime_str, directory):
    videofile_name = 'date_and_time.csv'
    filepath = os.path.join(directory, videofile_name)
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([datetime_str])

def write_bonsai_filenames(datetime_str, directory):
    ''' these are the names of the files that Bonsai will
    save the data to. They are saved in the Bonsai directory in 
    csv files. The csv files are: 1) videofile_name.csv, 2)
    videoTS_FileName.csv, 3) cropTimes_FileName.csv, 4) 
    cropValues_FileName.csv, 5) pulseTS_FileName.csv '''

    # 1) video file
    videofile_name = 'video_' + datetime_str + '.avi'
    filepath = os.path.join(directory, 'video_FileName.csv')
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([videofile_name])

    # 2) video timestamps
    videoTS_filename = 'videoTS_' + datetime_str + '.csv'
    filepath = os.path.join(directory, 'videoTS_FileName.csv')
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([videoTS_filename])

    # 3) crop times
    cropTimes_filename = 'cropTimes_' + datetime_str + '.csv'
    filepath = os.path.join(directory, 'cropTimes_FileName.csv')
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([cropTimes_filename])   
    
    # 4) crop values
    cropValues_filename = 'cropValues_' + datetime_str + '.csv'
    filepath = os.path.join(directory, 'cropValues_FileName.csv')
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([cropValues_filename])
    
    # 5) pulse timestamps
    pulseTS_filename = 'pulseTS_' + datetime_str + '.csv'
    filepath = os.path.join(directory, 'pulseTS_FileName.csv')
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([pulseTS_filename])


def write_bonsai_crop_params(params, directory):
    filename = 'cropNums.csv'
    filepath = os.path.join(directory, filename)
    # write the crop parameters to a csv file as 
    # a column 
    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for value in params:
            writer.writerow([value])
    

def delete_bonsai_csv(directory):
    file_substr = ['cropTimes', 'cropValues', 'pulseTS', 
                   'video', 'videoTS']
    for f in file_substr:
        file = f + '_FileName.csv'
        os.remove(os.path.join(directory, file))

     
if __name__ == "__main__":
    
    # for testing
    # load platform_coordinates
    map_path = 'D:/testFolder/pico_robots/map'
    with open(map_path + '/platform_coordinates.pickle', 'rb') as handle:
        platform_coordinates = pickle.load(handle)

    # crop_coordinates
    crop_coor = (421, 247, 600, 600) 

    # possible_platforms
    possible_platforms = [61, 80.0, 52.0] 
    
    host = '0.0.0.0'  # server's IP address
    port = 8000  # UDP port
    buffer_size = 1024
    n = 200  # Number of previous data points to store

    receiver = Animal(host, port, buffer_size, n)

    receiver.find_new_platform(possible_platforms, 61, platform_coordinates, crop_coor, 1)

    current_platform = receiver.get_current_platform()
    print(current_platform)

    print('sleeping')
    time.sleep(1)
    print('executing again')
    
    min_platform_dura = 2
    receiver.find_new_platform(possible_platforms, 61, 
                               platform_coordinates, crop_coor, min_platform_dura)

    current_platform = receiver.get_current_platform()
    print(current_platform)
