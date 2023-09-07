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
from typing import Any
from configurations import read_yaml
from tkinter import filedialog
import create_path as cp 
import copy


# robot definition
class Robot:
    def __init__(self, robot_id, ip_address, port_number, position, orientation, state, map):
        self.id = robot_id
        self.ip_address = ip_address
        self.port = port_number
        self.position = position
        self.orientation = orientation
        self.state = state # stationary or moving
        self.rings = cp.get_rings(self.position, map)

    @classmethod
    def from_yaml(cls, robot_id, yaml_data):
        ip_address = yaml_data['ip_address']
        port_number = yaml_data['port']
        position = 0
        orientation = 0
        state = 'stationary'
        return cls(robot_id, ip_address, port_number, position, orientation, state)

    def set_new_position(self, new_position):
        self.position = new_position
    
    def set_new_orientation(self, new_orientation):
        self.orientation = new_orientation

    def __str__(self):
        return (
            f'Robot {self.id} at {self.ip_address}, port {self.port} '
            f'is at position {self.position} and orientation {self.orientation}.'
        )

class Robots:
    def __init__(self):
        self.members = {}

    # def add_robot(self, robot_ind, robot_init):
    #    self.items[f'robot{robot_ind+1}'] = Robot.from_yaml(robot_ind+1, 
    #                                robot_init[f'robot{robot_ind+1}']) 

    def add_robot(self, robot):
        self.members[f'robot{robot.id}'] = robot   

    def add_robots(self, robot_list):
        for robot in robot_list:
            self.add_robot(robot)
       
        
    def get_stat_robot(self):
        for r in self.members:
            if self.members[r].state == 'stationary':
                return self.members[r]
            
    def get_moving_robots(self):
        robots_dict = copy.deepcopy(self.members)
        for r in robots_dict:
            if robots_dict[r].state == 'stationary':
                # remove stationary robot from dictionary
                robots_dict.pop(r)
                return robots_dict

    

def initialize_robots_as_dict(yaml_dir=None, positions=None, orientations=None):

    # yaml_dir = '/media/jake/LaCie/robot_maze_workspace'
    if yaml_dir is None:
        # ask user to select directory from gui
        yaml_dir = filedialog.askdirectory()


    robot_init = read_yaml(yaml_dir)

    robots = {}

    for r in range(3):
        robots[f'robot{r+1}'] = Robot.from_yaml(r+1, robot_init[f'robot{r+1}'])

        if positions is None:
            # ask user for new position and orientation
            robots[f'robot{r+1}'].set_new_position(input('Enter new position: '))
            robots[f'robot{r+1}'].set_new_orientation(input('Enter new orientation (0, 60, 120, 180, 240, 300): '))

        else:
            robots[f'robot{r+1}'].set_new_position(positions[r])
            robots[f'robot{r+1}'].set_new_orientation(orientations[r])

    return robots




def get_robot_positions(robots):
    # get the positions of the robots from the dict of robot objects.
    robot_positions = []
    for r in range(3):
        robot_positions.append(robots[f'robot{r+1}'].position)
    return robot_positions