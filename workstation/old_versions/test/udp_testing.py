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

    def store_data(self, data):
        # Add the new data point to the buffer
        self.data_buffer.append(data)
        
        # Ensure the buffer does not exceed 'n' data points
        if len(self.data_buffer) > self.n:
            self.data_buffer.pop(0)  # Remove the oldest data point

    def receive_data(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.bind((self.host, self.port))
            while True:
                data, _ = udp_socket.recvfrom(self.buffer_size)
                # Process and store the received data
                self.store_data(data)

host = '0.0.0.0'  # server's IP address
port = 8000  # UDP port
buffer_size = 1024
n = 100  # Number of previous data points to store

receiver = Animal(host, port, buffer_size, n)

import threading
data_receiver_thread = threading.Thread(target=receiver.receive_data)
data_receiver_thread.start()

while True:
    print(receiver.data_buffer)
