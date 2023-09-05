''' 
Generates the platform map required by the robots. The map is a numpy array
and is saved in a .csv file. 
Note that this code was translated from Matlab using Copilot in August, 2023; it may 
contain bugs that might be revealed if maze geometry is changed, so use caution!
Also, note that the current maze has n_rows = 26 and n_cols = [9, 10].
Finally, note that because the map contains nan values, it is a float array, not an int array.
'''

import numpy as np
import os
import tkinter as tk
from tkinter import filedialog

def generate_map(n_rows, n_cols, directory=None):
    if len(n_cols) == 2:
        n_cols_for_matrix = sum(n_cols)
        platform_map = np.full((n_rows, n_cols_for_matrix), np.nan)
        
        last_plat = 0
        for i in range(n_rows):
            if i > 0:
                last_plat = platforms[-1]
            
            if i % 2 == 0:
                platforms = last_plat + np.arange(1, n_cols[0]+1)
                
                if n_cols[0] < n_cols[1]:
                    platform_map[i, 1::2] = platforms
                else:
                    platform_map[i, 0::2] = platforms
                    
            else:
                platforms = last_plat + np.arange(1, n_cols[1]+1)
                
                if n_cols[0] < n_cols[1]:
                    platform_map[i, 0::2] = platforms
                else:
                    platform_map[i, 1::2] = platforms
                    
    else: # NOT SURE IF THIS WORKS, CHECK IF NEEDED!!!!
        platform_map = np.full((n_rows, n_cols*2), np.nan)
        
        for i in range(n_rows):
            if i % 2 == 0:
                platform_map[i, 1::2] = n_cols*(i) + np.arange(1, n_cols+1)
            else:
                platform_map[i, 0::2] = n_cols*(i) + np.arange(1, n_cols+1)

    # save platform map to csv file
    save_map('platform_map.csv', platform_map, directory)

    return platform_map

def open_map(map=None, directory=None):
    if directory is None:
        # ask user to select directory from gui
        root = tk.Tk()
        root.withdraw()
        print('Select directory containing map')
        directory = filedialog.askdirectory()
        
    if map is None:
        filepath = os.path.join(directory, 'platform_map.csv')
    else:
        filepath = os.path.join(directory, map + '.csv')
    
    # load platform map from csv file
    platform_map = np.loadtxt(filepath, delimiter=',')

    return platform_map

def get_rows_and_cols_to_exclude(platform_map, start_platform, stop_platform, extra_row):
    # find the row and column indices of the start and stop platforms, returned as integers
    start_row, start_col = np.argwhere(platform_map == start_platform)[0]
    stop_row, stop_col = np.argwhere(platform_map == stop_platform)[0]

    if extra_row != 0:
        stop_row = stop_row + extra_row

    # find the rows and columns to exclude from the top, bottom, left, and right
    rows_to_exclude = [start_row, platform_map.shape[0] - stop_row - 1]
    cols_to_exclude = [start_col, platform_map.shape[1] - stop_col - 1]

    return rows_to_exclude, cols_to_exclude


def restrict_map(platform_map, start_platform, stop_platform, extra_row=0, directory=None):
    # rows_cols_to_exclude is a list of integers, with (in order) the rows to exclude
    # from the top and bottom, and the columns to exclude from the left and right.
    # Currently, we are excluding the top 4 and bottom 4 rows, and the left 5 and right 3 columns.
    
    rows_to_exclude, cols_to_exclude = \
        get_rows_and_cols_to_exclude(platform_map, start_platform, stop_platform, extra_row)


    restricted_map = platform_map.copy()
    # save excluded platforms as a list
    restricted_map = restricted_map[rows_to_exclude[0]:-rows_to_exclude[1],
                                    cols_to_exclude[0]:-cols_to_exclude[1]]

    excluded_plats = []  
    excluded_plats_temp = []
    excluded_plats_temp.append(platform_map[:rows_to_exclude[0],:])    
    excluded_plats_temp.append(platform_map[-rows_to_exclude[1]:,:])    
    excluded_plats_temp.append(platform_map[:,:cols_to_exclude[0]])
    excluded_plats_temp.append(platform_map[:,-cols_to_exclude[1]:])
      
    # append to excluded_plats  
    for i in range(4):
        excluded_plats.extend(excluded_plats_temp[i][~np.isnan(excluded_plats_temp[i])])
    # cast excluded_plats as integers and sort in ascending order
    excluded_plats = np.array(excluded_plats, dtype=int)
    excluded_plats = np.sort(excluded_plats)

    save_map('restricted_map.csv', restricted_map, directory=None)
    
    return restricted_map, excluded_plats

def save_map(filename, map, directory=None):
    if directory is None:
        # ask user to select directory from gui
        root = tk.Tk()
        root.withdraw()
        directory = filedialog.askdirectory()

    filepath = os.path.join(directory, filename)
    np.savetxt(filepath, map, delimiter=',')

    return

if __name__ == '__main__':
    platform_map = generate_map(26, [9, 10])
    restricted_map, _ = restrict_map(platform_map, 41, 217, extra_row=1)