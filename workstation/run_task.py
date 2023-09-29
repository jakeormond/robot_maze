'''
Code to run the task. In the future, this will be implemented as a gui.

Note that the cropping parameters are sent to Bonsai by csv file; we don't
need to delete the csv file, as this is handled by Bonsai after reading it.
'''

from configurations import read_yaml
from robot_class import Robot, Robots
from create_path import Paths
from choices_class import Choices
import platform_map as mp
from send_over_socket import send_over_sockets_threads
from animal import Animal, write_bonsai_filenames, write_bonsai_crop_params, delete_bonsai_csv
import pickle
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

with open(map_dir + '/platform_coordinates.pickle', 'rb') as handle:
    platform_coordinates = pickle.load(handle)

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
write_bonsai_filenames(datetime_str, directory)

# get initial cropping parameters, and write to csv
crop_nums = map.get_crop_nums([robots.get_stat_robot().position])
write_bonsai_crop_params(crop_nums, directory)

# create animal instance necessary for tracking
host = '0.0.0.0'  # server's IP address
port = 8000  # UDP port
buffer_size = 1024
n = 200  # Number of previous data points to store
animal = Animal(host, port, buffer_size, n)

# tell user to start video, and then ephys, and then any 
# button to start the trial
print('Start video and ephys')
input('\nPress any key to continue')

# set some variables
# difficulty = 'easy'
difficulty = 'hard'

# MAIN LOOP
choice_counter = 1
while True:
    # pick next platforms and construct paths as well as commands and durations
    paths = Paths(robots, map, choices=trial_data)
    # display figure of paths
    paths.plot_paths()

    # if this is the trial start, we can send the full commands,
    # otherwise, we need to turn the robots, and then make sure 
    # the animal hasn't changed its mind!
    if choice_counter != 1:
        # split off the first paths
        intial_turns, paths = paths.split_off_initial_turn()

    # send commands to robots. This can return 
    # data from the robots, but probably not necessary
    # THIS SHOULD INCLUDE ONLY THE FIRST TURNS
    send_over_sockets_threads(robots.get_moving_robots(), paths)

    # update robot positions and directions
    start_platform, positions = robots.update_positions(paths)    

    # SO WE CAN MAKE SURE THE ANIMAL DIDN'T MOVE
    # monitor the tracking data coming from Bonsai to determine
    # when the animal's made its decision. 
    animal.find_new_platform(positions, start_platform, platform_coordinates, crop_coor)



    








# save the choice history to file
trial_data.save_choices(data_dir)







# close figure
cp.close_paths_plot(paths_fig)

delete_bonsai_csv(directory)
