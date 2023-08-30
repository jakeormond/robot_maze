'''
Code to run the task. In the future, this will be implementd as a gui.
'''

from configurations import read_yaml
from robot_class import Robot
from choices_class import Choices

# create robot instances in a dictionary
yaml_dir = '/media/jake/LaCie/robot_maze_workspace'
robot_init = read_yaml(yaml_dir)

robots = {}

for r in range(3):
    robots[f'robot{r+1}'] = Robot.from_yaml(r+1, robot_init[f'robot{r+1}'])

    # ask user for new position and orientation
    robots[f'robot{r+1}'].set_new_position(input('Enter new position: '))
    robots[f'robot{r+1}'].set_new_orientation(input('Enter new orientation (0, 60, 120, 180, 240, 300): '))

# set goal position
goal_position = input('Enter goal position: ')

# initialized data storage
trial_data = Choices()
data_dir = '/media/jake/LaCie/robot_maze_workspace'

# 
