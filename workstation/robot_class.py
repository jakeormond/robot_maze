''' 
Define the robot class. These instances will be used to represent the robots in 
the workstation control program. 
They should contain the following attributes: 1) the robot's ID, 2) the robot's 
ip address, 3) the robot's current position, 4) the robot's current orientation.
They should also contain the following methods: 1) a method to set the robot's
new position, 2) a method to set the robot's new orientation, 3) a method to
send a command to the robot and receive data from it (note that this method 
may ultimately be implemented independently of the robot class to deal with 
multiple robots at once)
'''

import socket

# robot definition
class Robot:
    def __init__(self, robot_id, ip_address, port_number, position, orientation):
        self.robot_id = robot_id
        self.ip_address = ip_address
        self.port = port_number
        self.position = position
        self.orientation = orientation

    @classmethod
    def from_yaml(cls, robot_id, yaml_data):
        ip_address = yaml_data['ip_address']
        port_number = yaml_data['port']
        position = 0
        orientation = 0
        return cls(robot_id, ip_address, port_number, position, orientation)

    def set_new_position(self, new_position):
        self.position = new_position
    
    def set_new_orientation(self, new_orientation):
        self.orientation = new_orientation

    def send_command(self, string_input):
        bytes_to_send = bytes(string_input, 'utf8')
        received_data = []
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.ip_address, self.port))
            s.sendall(bytes_to_send)
           
            counter = 0
            
            while True:
                counter += 1
                print('counter : ', counter)
                data = s.recv(1024)

                # check if data is empty
                if not data:
                    break
                
                print(f"Received {data!r}")
                print(data)
                
                data = data.decode('utf8')
                # split data on comma
                data = data.split(',')
                # check is any elements are empty and remove them
                data = [x for x in data if x != '']

                # append to received data
                received_data.extend(data)

        # print received data
        print(received_data)
        return received_data
    
    def __str__(self):
        return (
            f'Robot {self.robot_id} at {self.ip_address}, port {self.port} '
            f'is at position {self.position} and orientation {self.orientation}.'
        )
