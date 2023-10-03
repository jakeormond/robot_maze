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

# CONSTANTS
min_platform_dura_new = 2  # minimum duration animal must be on new platform to register choice
min_platform_dura_verify = 1  # minimum duration animal must be on  platform to verify choice
                            # after robots have made their initial turns 

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

#initialize data storage
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
# save initial crop params to trial_data
trial_data.save_initial_crop_params(crop_nums)

# create animal instance necessary for tracking
host = '0.0.0.0'  # server's IP address
port = 8000  # UDP port
buffer_size = 1024
n = 200  # Number of previous data points to store
animal = Animal(host, port, buffer_size, n)

# tell user to start video, and then ephys, and then any 
# button to start the trial
input('\nStart video and ephys - press any key to continue')

# set some variables
# difficulty = 'easy'
difficulty = 'hard'

# MAIN LOOP
choice_counter = 1
start_platform = robots.members['robot1'].position

possible_platforms = robots.get_positions()
while True:
    # if animal is at goal, we just need to move the other 2 robots away
    if choice_counter != 1 and chosen_platform == map.goal_position:
            paths = Paths(robots, map, task='move_away')
    else:
        # pick next platforms and construct paths as well as commands and durations
        paths = Paths(robots, map, choices=trial_data)

    # if this is the trial start, we can send the full commands,
    # otherwise, we need to turn the robots, and then make sure 
    # the animal hasn't changed its mind from the last choice!
    if choice_counter != 1:
        while True:
            # split off the first paths
            initial_turns = paths.split_off_initial_turn()
            if initial_turns is None: # if there are no initial turns
                break

            # send commands to robots. This can return 
            # data from the robots, but probably not necessary
            # THIS SHOULD INCLUDE ONLY THE FIRST TURNS
            # robot positions are updated in this function
            send_over_sockets_threads(robots, initial_turns)
            robots.update_orientations(initial_turns)  

            # SO WE CAN MAKE SURE THE ANIMAL DIDN'T MOVE
            # monitor the tracking data coming from Bonsai to determine
            # when the animal's made its decision. 
            verified_platform, _ = animal.find_new_platform(possible_platforms, start_platform, 
                               platform_coordinates, crop_nums, min_platform_dura_verify)
                       
            if chosen_platform != verified_platform:
                print('Animal changed its mind!')
                print(f'new choice is platform {verified_platform}')
                
                # update the choice history
                trial_data.register_choice(verified_platform, chosen_platform)
                
                # update robots, the stationary robot becomes moving, and the 
                # the verified_platform robot becomes stationary
                stat_robot_key = robots.get_robot_key_at_position(verified_platform)
                robots.members[stat_robot_key].set_new_state('stationary')

                non_stat_robot_key = robots.get_key_at_position(chosen_platform)
                robots.members[non_stat_robot_key].set_new_state('moving')

                # reset current_platform
                chosen_platform = verified_platform

                # recompute the paths and send the new commands
                paths.close_paths_plot()
                paths = Paths(robots, map, choices=trial_data)

            else:
                
                start_platform = chosen_platform
                break

    # plot the paths
    paths.plot_paths(robots, map)

    # send the remaining commands to robots.
    send_over_sockets_threads(robots, paths)
    robots.update_positions(paths)    

    # if at the goal, then trial is done
    if choice_counter != 1:
        if chosen_platform == map.goal_position:
            print('Animal reached goal!')
            print('End of trial')
            break   

    # get new crop parameters
    crop_nums = map.get_crop_nums(robots.get_positions())
    write_bonsai_crop_params(crop_nums, directory)   

    # start the choice and save crop params
    trial_data.start_choice(start_platform)
    trial_data.save_crop_params(crop_nums)

    # robots are updated in the send_over_sockets_threads function
    possible_platforms = robots.get_positions()

    # get the animal's choice    
    chosen_platform, unchosen_platform = animal.find_new_platform(possible_platforms, start_platform, 
                               platform_coordinates, crop_nums, min_platform_dura_new)
    trial_data.register_choice(chosen_platform, unchosen_platform)
    choice_counter += 1    
    
    # update robot states
    stat_robot_key = robots.get_robot_key_at_position(chosen_platform)
    robots.members[stat_robot_key].set_new_state('stationary')

    non_stat_robot_key = robots.get_robot_key_at_position(start_platform)
    robots.members[non_stat_robot_key].set_new_state('moving')

    # close plot of paths
    paths.close_paths_plot()

# save the choice history to file
trial_data.save_choices(data_dir)






