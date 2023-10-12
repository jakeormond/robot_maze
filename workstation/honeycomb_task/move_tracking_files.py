''' move the tracking files to the corresponding behavioural data folder '''

import os
import shutil
import glob
import pandas as pd
import numpy as np
import re
import tkinter as tk

def move_tracking_files(animal_num=None, starting_dir=None, destination_dir=None):
    if animal_num is None:
        animal_num = input('Enter animal number: ')
    
    if starting_dir is None:
        # allow user to select the starting directory using a GUI
        root = tk.Tk()
        root.withdraw()
        starting_dir = tk.filedialog.askdirectory()
    
    if destination_dir is None:
        # allow user to select the destination directory using a GUI
        root = tk.Tk()
        root.withdraw()
        destination_dir = tk.filedialog.askdirectory()

    # find all files in the starting directory, without including subdirectories
    files = os.listdir(starting_dir)

    # find video files begin with 'video_' and end with '.avi'
    video_files = [f for f in files if re.match(r'video_\d{4}-\d{2}-\d{2}_\d{2}\.\d{2}\.\d{2}\.avi', f)]

    # csv files begin with: 'videoTS_', 'cropTimes_', 'cropValues_', 
    # 'pulseTS_', 'dlcOut_', and end with '.csv'
    csv_files = [f for f in files if re.match(r'(videoTS_|cropTS_|cropValues_|pulseTS_|dlcOut_)\d{4}-\d{2}-\d{2}_\d{2}\.\d{2}\.\d{2}\.csv', f)]
     
     # in the destination directory, create a folder for the video and csv files 
     # if it hasn't already been created
    folder_name = 'video_and_csv_files'
    if not os.path.exists(os.path.join(destination_dir, folder_name)):
        os.mkdir(os.path.join(destination_dir, folder_name))

    # move the video files to the destination directory
    for f in video_files:
        shutil.move(os.path.join(starting_dir, f), os.path.join(destination_dir, folder_name))
    
    # move the csv files to the destination directory
    for f in csv_files:
        shutil.move(os.path.join(starting_dir, f), os.path.join(destination_dir, folder_name))

    # remove the file date_and_time.csv from the starting directory
    os.remove(os.path.join(starting_dir, 'date_and_time.csv'))


