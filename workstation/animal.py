''' 
The animal class contains the animal's position calculated 
from the tracking data. It also contains the animal's choice.
'''
import socket
import os
import csv
import struct
import numpy as np

class Animal:
    def __init__(self, host, port, buffer_size, n):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.n = n
        self.data_buffer = []

    def receive_data(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.bind((self.host, self.port))
            while True:
                data, _ = udp_socket.recvfrom(self.buffer_size)
                # Process and store the received data
                self.store_data(data)

    def store_data(self, data):
        # Add the new data point to the buffer
        self.data_buffer.append(data)
        
        # Ensure the buffer does not exceed 'n' data points
        if len(self.data_buffer) > self.n:
            self.data_buffer.pop(0)  # Remove the oldest data point

    def get_recent_data(self):
        return self.data_buffer
    
    def parse_most_recent_data(self):
        received_data = self.data_buffer[-1]
        parsed_data = parse_data(received_data)

        return parsed_data

    def parse_all_recent_data(self):
        received_data = self.data_buffer

        # get the number of packets
        num_packets = len(received_data)

        # initialize array to store the parsed data
        parsed_data = np.zeros((num_packets, 6))

        # loop through the packets and parse the data
        for i in range(num_packets):
            parsed_data[i, :] = parse_data(received_data[i])
        
        return parsed_data

def parse_data(received_data):
    parsed_data = np.zeros((6))

    indices = [18, 22, 26, 30, 34, 38]

    for i, index in enumerate(indices):
        parsed_data[i] = int.from_bytes(received_data[index:index+2], byteorder='big', signed=True)
    
    return parsed_data
       
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
    host = '0.0.0.0'  # server's IP address
    port = 8000  # UDP port
    buffer_size = 1024
    n = 100  # Number of previous data points to store

    receiver = Animal(host, port, buffer_size, n)

    # Start the data receiver in a separate thread or process
    # You may use threading or multiprocessing module for this

    # Example: Create a separate thread to run the data receiver
    import threading
    data_receiver_thread = threading.Thread(target=receiver.receive_data)
    data_receiver_thread.start()

    # Now, you can access the recent data from the receiver object in your main program
    while True:
        print(receiver.data_buffer)