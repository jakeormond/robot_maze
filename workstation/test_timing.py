'''
Code to run the task. In the future, this will be implemented as a gui.

Note that the cropping parameters are sent to Bonsai by csv file; we don't
need to delete the csv file, as this is handled by Bonsai after reading it.
'''

from honeycomb_task.robot import Robots
from honeycomb_task.create_path import Paths
from honeycomb_task.choices import Choices
from honeycomb_task.platform_map import Map
from honeycomb_task.send_over_socket import send_over_sockets_threads
from honeycomb_task.animal import Animal, write_date_and_time, write_bonsai_crop_params
from honeycomb_task.move_tracking_files import honeycomb_task_file_cleanup, create_directory
from honeycomb_task.plot_paths import Plot
import os
import datetime
import pandas as pd
# import matplotlib.pyplot as plt
import copy
import time
# plt.ion

# CONSTANTS
min_platform_dura_new = 0.1  # minimum duration animal must be on new platform to register choice

# top level folder
top_dir = 'D:/testFolder'


# create robot instances in a dictionary
# yaml_dir = '/media/jake/LaCie/robot_maze_workspace'
# yaml_dir = 'D:/testFolder/pico_robots/yaml'
yaml_dir = 'C:/Users/Jake/Documents/robot_code/yaml'
robots = Robots.from_yaml(yaml_dir, positions=[90,99,100], orientations=[0, 0, 0])

# load map and set goal position
# platform coordinates are also stored in the map object
# map_dir = 'D:/testFolder/pico_robots/map'
map_dir = 'C:/Users/Jake/Documents/robot_code/robot_maze/workstation/map_files'
map = Map(directory=map_dir)

# get crop coordinates
# crop_nums = map.get_crop_nums([robots.get_stat_robot().position])
# crop_nums = map.get_crop_nums(robots.get_positions()) 
# write_bonsai_crop_params(crop_nums, top_dir)

# create animal instance necessary for tracking
# HOST = '0.0.0.0'  # server's IP address
# PORT = 8000  # UDP port
# buffer_size = 1024
# n = 200  # Number of previous data points to store
# animal = Animal(HOST, PORT, buffer_size, n)


############ TEST TRACKING TIME ################
# tell user to start video, and then ephys, and then any 
# button to start the trial
# input('\nStart video - press any key to continue')
# # determine the time duration to find the animal's choice
# start = time.time()
# # get the animal's choice    
# chosen_platform, unchosen_platform = animal.find_new_platform([99, 100], 90, 
#                         map.platform_coordinates, crop_nums, min_platform_dura_new)
# stop_time = time.time() - start
# print(f'Animal chose platform {int(chosen_platform)} in {stop_time} seconds')


######### TEST TIME TO SEND OVER SOCKET ##########

next_positions = [80, 81]
start = time.time()
paths = Paths(robots, map, next_positions=next_positions)
stop_time = time.time() - start
print(f'time to create paths: {stop_time} seconds')

robots.update_positions(paths)
start = time.time()
send_over_sockets_threads(robots, paths, start_time=start)      
stop_time = time.time() - start
print(f'time to send over socket: {stop_time} seconds') 
pass





