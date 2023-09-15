'''
Code to run the task. In the future, this will be implemented as a gui.
'''

from configurations import read_yaml
from robot_class import Robot
import create_path as cp
from create_path import Paths
from choices_class import Choices
from robot_class import Robots
from cropping import get_crop_nums
import platform_map as mp
import send_over_socket as sos
import tkinter as tk
from tkinter import filedialog
import os
import csv

# create robot instances in a dictionary
yaml_dir = '/media/jake/LaCie/robot_maze_workspace'
robots = Robots.from_yaml(yaml_dir)

# load map and set goal position
map = mp.Map(directory=yaml_dir)
map.set_goal_position(input('Enter goal position: '))

# initialize data storage
trial_data = Choices()
filename = trial_data.name
data_dir = '/media/jake/LaCie/robot_maze_workspace'

# save filenames for Bonsai to use and set Bonsai path
# ask user to select directory
root = tk.Tk()
root.withdraw()
directory = filedialog.askdirectory(title='Select Bonsai directory')

# write filename to a csv file in the Bonsai directory
filepath = os.path.join(directory, 'videofile_name.csv')
with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow([filename]) 

# get initial cropping parameters
# first, get the robot positions
robot_positions = robots.get_positions()
plat_coor_dir = data_dir
plat_coor = get_plat_coor(robot_positions, plat_coor_dir) # need to write this code still
crop_nums = get_crop_nums(robot_positions, plat_coor)
# write crop_nums to a csv file in the Bonsai directory. If the file already
# exists, overwrite it.
filepath = os.path.join(directory, 'crop_nums.csv')
with open(filepath, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(crop_nums)  

# tell user to start video, and then ephys, and then any 
# button to start the trial
print('Start video and ephys')
input('\nPress any key to continue')

# delete the csv file in the Bonsai directory as it has now been read
os.remove(filepath)

# set some variables
# difficulty = 'easy'
difficulty = 'hard'

# load map

# MAIN LOOP
while True:
    # pick next platforms
    next_platforms = cp.get_next_positions(robots, map, trial_data, difficulty)

    # construct paths as well as commands and durations
    paths = Paths(robots, next_platforms, map)

    # display figure of paths
    paths.plot_paths()

    # send commands to robots. This can return 
    # data from the robots, but probably not necessary
    # THIS SHOULD INCLUDE ONLY THE FIRST TURNS
    sos.send_over_sockets_select(robots, paths) 

    # SO WE CAN MAKE SURE THE ANIMAL DIDN'T MOVE
    # monitor the tracking data coming from Bonsai to determine
    # when the animal's made its decision. 



    








# save the choice history to file
trial_data.save_choices(data_dir)







    # close figure
    cp.close_paths_plot(paths_fig)

