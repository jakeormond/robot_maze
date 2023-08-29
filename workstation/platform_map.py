''' 
Generates the platform map required by the robots. The map is a numpy array
and is saved in a .csv file. 
Note that this code was translated from Matlab using Copilot in August, 2023; it may 
contain bugs that might be revealed if maze geometry is changed, so use caution!
Also, note that the current maze has n_rows = 26 and n_cols = [9, 10].
Finally, note that because the map contains nan values, it is a float array, not an int array.
'''

import numpy as np

def generate_map(n_rows, n_cols):
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
    np.savetxt('platform_map.csv', platform_map, delimiter=',')    
    return platform_map

def restrict_map(platform_map, rows_cols_to_exclude):
    # rows_cols_to_exclude is a list of integers, with (in order) the rows to exclude
    # from the top and bottom, and the colums to exclude from the left and right.
    # Currently, we are excluding the top 4 and bottom 4 rows, and the left 5 and right 3 columns.
    
    restricted_map = platform_map.copy()
    # save excluded platforms as a list
    excluded_plats = []
    
    for i in range(len(rows_cols_to_exclude)):
        if i == 0:
            restricted_map = restricted_map[rows_cols_to_exclude[0]:,:]
            excluded_plats_temp = platform_map[:rows_cols_to_exclude[0]-1,:]
        
        if i == 1:
            restricted_map = restricted_map[0:-rows_cols_to_exclude[1]:,:]
            excluded_plats_temp = platform_map[-rows_cols_to_exclude[1],:]
        
        if i == 2:
            restricted_map = restricted_map[:,rows_cols_to_exclude[2]:]
            excluded_plats_temp = platform_map[:,:rows_cols_to_exclude[2]-1]
        
        if i == 3:
            restricted_map = restricted_map[:,:-rows_cols_to_exclude[3]]         
           
        # append to excluded_plats  
        excluded_plats.extend(excluded_plats_temp[~np.isnan(excluded_plats_temp)])

        # save restricted map to csv file
        np.savetxt('restricted_map.csv', restricted_map, delimiter=',')

    return restricted_map, excluded_plats

