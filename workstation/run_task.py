'''
Code to run the task. In the future, this will be implemented as a gui.

Note that the cropping parameters are sent to Bonsai by csv file; we don't
need to delete the csv file, as this is handled by Bonsai after reading it.
'''

# from honeycomb_task.configuration import read_yaml
from honeycomb_task.robot import Robots
from honeycomb_task.create_path import Paths
from honeycomb_task.choices import Choices
from honeycomb_task.platform_map import Map
from honeycomb_task.send_over_socket import send_over_sockets_threads
from honeycomb_task.animal import Animal, write_bonsai_filenames, write_bonsai_crop_params, delete_bonsai_csv
import pickle
import os
import datetime
import pandas as pd

# CONSTANTS
min_platform_dura_new = 2  # minimum duration animal must be on new platform to register choice
min_platform_dura_verify = 1  # minimum duration animal must be on  platform to verify choice
                            # after robots have made their initial turns 

# top level folder
top_dir = 'D:/testFolder'

# ask user to enter the animal numnber
animal_num = input('Enter animal number: ')
# get the date without the time
datetime_str = datetime.datetime.now().strftime('%Y-%m-%d')
# create folder if it doesn't yet exist
data_dir = os.path.join(top_dir, 'robot_maze_behaviour', f'Rat_{animal_num}', datetime_str)
# if any of these nested folders don't exist, create them
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# load previous choices
previous_choices = Choices(directory=data_dir)   
# initialize new data storage
trial_data = Choices()
datetime_str = trial_data.name

# create robot instances in a dictionary
# yaml_dir = '/media/jake/LaCie/robot_maze_workspace'
yaml_dir = 'D:/testFolder/pico_robots/yaml'
robots = Robots.from_yaml(yaml_dir)

# load map and set goal position
# platform coordinates are also stored in the map object
map_dir = 'D:/testFolder/pico_robots/map'
map = Map(directory=map_dir)
map.set_goal_position(input('Enter goal position: '))

with open(map_dir + '/platform_coordinates.pickle', 'rb') as handle: # MAYBE I SHOULD ADD PLATFORM_COORDINATES TO MAP CLASS?????
    platform_coordinates = pickle.load(handle)

# save filenames for Bonsai to use and set Bonsai path
write_bonsai_filenames(datetime_str, top_dir)

# get initial cropping parameters, and write to csv
crop_nums = map.get_crop_nums([robots.get_stat_robot().position])
write_bonsai_crop_params(crop_nums, top_dir)
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
        # concatenate trial data to the previous choices for the day
        previous_choices.data = pd.concat([previous_choices.data, trial_data.data], ignore_index=True)
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
                # set the start platform to the chosen platform
                print('no initial turns')
                start_platform = chosen_platform
                verified_platform = chosen_platform
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

                non_stat_robot_key = robots.get_robot_key_at_position(chosen_platform)
                robots.members[non_stat_robot_key].set_new_state('moving')

                # reset current_platform
                chosen_platform = verified_platform

                # recompute the paths and send the new commands
                paths.close_paths_plot()
                paths = Paths(robots, map, choices=trial_data)

            else:
                print(f'Animal chose platform {int(verified_platform)}')
                start_platform = chosen_platform
                break

    # CHECKING FOR BUGS
    if choice_counter != 1 and verified_platform != chosen_platform:
        print('ERROR: verified platform does not match chosen platform')
        # pause execution
        input('Set a breakpoint, then press any key to continue')

    stat_robot = robots.get_stat_robot()
    # if stat_robot is an integer, then there is either 0 or more than one stationary robot
    if type(stat_robot) == int:
        print('ERROR: there are {stat_robot} stationary robots, but there should be only 1')
        # pause execution
        input('Set a breakpoint, then press any key to continue')
    # CHECKING FOR BUGS

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
    write_bonsai_crop_params(crop_nums, top_dir)   

    # start the choice and save crop params
    trial_data.start_choice(start_platform)
    trial_data.save_crop_params(crop_nums)

    # get the possible platforms
    possible_platforms = robots.get_positions()
    print(f'Start platform is {start_platform}')
    # choice platforms are the possible platforms minus the start platform
    choice_platforms = possible_platforms.copy()
    choice_platforms.remove(start_platform)
    print(f'Choice platforms are {int(choice_platforms[0])} and {int(choice_platforms[1])}')

    # get the animal's choice    
    chosen_platform, unchosen_platform = animal.find_new_platform(possible_platforms, start_platform, 
                               platform_coordinates, crop_nums, min_platform_dura_new)
    print(f'Animal chose platform {int(chosen_platform)}')
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






