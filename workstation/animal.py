''' 
The animal class contains the animal's position calculated 
from the tracking data. It also contains the animal's choice.
'''
import socket

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

if __name__ == "__main__":
    host = '0.0.0.0'  # Replace with your server's IP address
    port = 8000  # Replace with your desired UDP port
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
        recent_data = receiver.get_recent_data()
        # Process recent data as needed in your main program