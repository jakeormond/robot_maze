''' move the tracking files to the corresponding behavioural data folder '''

import os
import shutil
import re
import tkinter as tk

def create_directory(new_directory, parent_directory=None):
    if parent_directory is not None:
        # check for access to parent directory
        if not os.access(parent_directory, os.W_OK):
            raise ValueError(f'You do not have write access to {parent_directory}')
            return
    
    if not os.path.exists(new_directory):
        os.makedirs(new_directory)

def list_tracking_files(animal_num, starting_dir):
    # find all files in the starting directory, without including subdirectories
    files = os.listdir(starting_dir)

    # find video files begin with 'video_' and end with '.avi'
    video_files = [f for f in files if re.match(r'video_\d{4}-\d{2}-\d{2}_\d{2}\.\d{2}\.\d{2}\.avi', f)]

    # csv files begin with: 'videoTS_', 'cropTimes_', 'cropValues_', 
    # 'pulseTS_', 'dlcOut_', and end with '.csv'
    csv_files = [f for f in files if re.match(r'(videoTS_|cropTS_|cropValues_|pulseTS_|dlcOut_)\d{4}-\d{2}-\d{2}_\d{2}\.\d{2}\.\d{2}\.csv', f)]

    return video_files, csv_files

def move_tracking_files(animal_num=None, starting_dir=None, destination_dir=None, remove_from_starting_dir=False):    
    
    if animal_num is None:
        animal_num = input('Enter animal number: ')
    
    if starting_dir is None:
        # allow user to select the starting directory using a GUI
        root = tk.Tk()
        root.withdraw()
        starting_dir = tk.filedialog.askdirectory()
    
    video_files, csv_files = list_tracking_files(animal_num, starting_dir)

    if destination_dir is None:
        # allow user to select the destination directory using a GUI
        root = tk.Tk()
        root.withdraw()
        destination_dir = tk.filedialog.askdirectory()

    else: # check if we have access to the destination directory
        if not os.access(destination_dir, os.W_OK):
            raise ValueError(f'You do not have write access to {destination_dir}')
            return

    # in the destination directory, create a folder for the video and csv files 
    # if it hasn't already been created
    folder_name = 'video_and_csv_files'
    if not os.path.exists(os.path.join(destination_dir, folder_name)):
        os.mkdir(os.path.join(destination_dir, folder_name))

    # if remove_from_starting_dir is True, remove the files from the starting directory
    if remove_from_starting_dir:        
        for f in video_files:
            shutil.move(os.path.join(starting_dir, f), os.path.join(destination_dir, folder_name))
        
        # move the csv files to the destination directory
        for f in csv_files:
            shutil.move(os.path.join(starting_dir, f), os.path.join(destination_dir, folder_name))
    
    else:
        # copy the video files to the destination directory
        for f in video_files:
            shutil.copy(os.path.join(starting_dir, f), os.path.join(destination_dir, folder_name))
        
        # copy the csv files to the destination directory
        for f in csv_files:
            shutil.copy(os.path.join(starting_dir, f), os.path.join(destination_dir, folder_name))


def remove_file(directory, filename):
    os.remove(os.path.join(directory, filename))
    

def honeycomb_task_file_cleanup(animal_num, trial_data, top_dir, data_dir, date_str):
    # copy the tracking files to the remote server for long term storage
    server_dir = 'X:/Jake/robot_maze'
    server_data_dir = os.path.join(server_dir, 'robot_maze_behaviour', f'Rat_{animal_num}', date_str)
    create_directory(server_data_dir, server_dir)
    trial_data.save_choices(server_data_dir)
    move_tracking_files(animal_num=animal_num, starting_dir=top_dir, \
                        destination_dir=server_data_dir, remove_from_starting_dir=False)

    # move the tracking files to the data directory for local storage
    move_tracking_files(animal_num=animal_num, starting_dir=top_dir, \
                        destination_dir=data_dir, remove_from_starting_dir=True)

    remove_file(top_dir, 'date_and_time.csv')

