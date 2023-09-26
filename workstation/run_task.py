'''
Code to run the task. In the future, this will be implemented as a gui.
'''

from configurations import read_yaml
from robot_class import Robot, Robots
from create_path import Paths
from choices_class import Choices
import platform_map as mp
from send_over_socket import send_over_sockets_threads
import animal
import tkinter as tk
from tkinter import filedialog
import os
import csv

# create robot instances in a dictionary
# yaml_dir = '/media/jake/LaCie/robot_maze_workspace'
yaml_dir = 'D:/testFolder/pico_robots/yaml'
robots = Robots.from_yaml(yaml_dir)

# load map and set goal position
# platform coordinates are also stored in the map object
map_dir = 'D:/testFolder/pico_robots/map'
map = mp.Map(directory=map_dir)
map.set_goal_position(input('Enter goal position: '))

# initialize data storage
trial_data = Choices()
datetime_str = trial_data.name
# data_dir = '/media/jake/LaCie/robot_maze_workspace'
data_dir = 'D:/testFolder/robot_maze_behaviour'

# save filenames for Bonsai to use and set Bonsai path
# ask user to select directory
# root = tk.Tk()
# root.withdraw()
# directory = filedialog.askdirectory(title='Select Bonsai directory')
directory = 'D:/testFolder'
animal.write_bonsai_filenames(datetime_str, directory)

# get initial cropping parameters, and write to csv
crop_nums = map.get_crop_nums([robots.get_stat_robot().position])
animal.write_bonsai_crop_params(crop_nums, directory)

# tell user to start video, and then ephys, and then any 
# button to start the trial
print('Start video and ephys')
input('\nPress any key to continue')

# delete the csv file in the Bonsai directory as it has now been read
animal.delete_bonsai_csv(directory)

# set some variables
# difficulty = 'easy'
difficulty = 'hard'

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
    send_over_sockets_threads(robots.get_moving_robots(), paths)

    # update robot positions and directions
    robots.update_positions(paths)

    # SO WE CAN MAKE SURE THE ANIMAL DIDN'T MOVE
    # monitor the tracking data coming from Bonsai to determine
    # when the animal's made its decision. 
    get_choice_from_tracking(robots)



    








# save the choice history to file
trial_data.save_choices(data_dir)







# close figure
cp.close_paths_plot(paths_fig)

