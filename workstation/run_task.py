'''
Code to run the task. In the future, this will be implemented as a gui.
'''

from configurations import read_yaml
from robot_class import Robot
from choices_class import Choices
from robot_class import get_robot_positions, initialize_robots_as_dict
from cropping import getCropNums

# create robot instances in a dictionary
yaml_dir = '/media/jake/LaCie/robot_maze_workspace'
robots = initialize_robots_as_dict(yaml_dir, positions=None, orientations=None)

# set goal position
goal_position = input('Enter goal position: ')

# initialize data storage
trial_data = Choices()
data_dir = '/media/jake/LaCie/robot_maze_workspace'

# get initial cropping parameters
# first, get the robot positions
robot_positions = get_robot_positions(robots)
crop_nums = getCropNums(robot_positions, plat_coor)

