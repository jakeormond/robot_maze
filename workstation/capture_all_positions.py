'''
This code allows all platform positions to be captured and saved as jpeg images.
Later, these jpegs will be used to determine the platform positions in pixels;
this information is required for dynamic cropping of the video feed during 
data collection.
'''
import numpy as np
from configurations import read_yaml
from robot_class import Robot, initialize_robots_as_dict, get_robot_positions
from platform_map import open_map, restrict_map
from frame_capture import capture_frame
from tkinter import filedialog

def get_next_positions(platform_map, prev_positions, direction):

    n_pos = len(prev_positions)

    # get the number of rows and columns in the restricted map
    n_rows = platform_map.shape[0]
    n_cols = platform_map.shape[1]

    bottom_row, col = np.argwhere(platform_map == prev_positions[-1])[0]

    # if robot is on the last row and last column, stop
    if bottom_row == n_rows:
        if direction == 'right' and col == n_cols or \
            direction == 'left' and col == 0:
            
            return None
    
    # if robot on last column, move to the next set of rows and change direction
    if direction == 'right' and col == n_cols or \
        direction == 'left' and col == 0:
        
        new_rows = np.arrange(bottom_row + 2, bottom_row + (n_pos+1)*2, 2)
        next_positions = platform_map[new_rows, :]


        if direction == 'right':
            direction = 'left'
        else:
            direction = 'right'

        return next_positions
    
    # otherwise, move the robots left or right




    




# load the platform map
platform_map = open_map(directory=None)
start_platform = 41
stop_platform = 217

# find rows and columns to exclude (robot can't drive there because of curtains)
restricted_map, excluded_plats = \
    restrict_map(platform_map, start_platform, stop_platform, directory=None)

# get the number of rows and columns in the restricted map
n_rows = restricted_map.shape[0]
n_cols = restricted_map.shape[1]

n_robots = 3
travel_direction = 'right' # travel direction switches to 'left' when the robots reach the right side of the maze

# start_pos is a 3 element vector taken using current_rows and current_col as indices into platform_map
start_pos = restricted_map[[0, 2, 4], 0].astype(int)
orientations = np.array([0, 0, 0])

# create the robot instances
yaml_dir = '/media/jake/LaCie/robot_maze_workspace'
robot_init = read_yaml(yaml_dir)
robots = initialize_robots_as_dict(yaml_dir, start_pos, orientations)

# select directory for saving images
directory = filedialog.askdirectory()

# loop through the groups of platform positions, capturing images at each position
counter = 0
while True:
    # capture image
    positions = get_robot_positions(robots)

    filename = f'platforms_{positions[0]}_{positions[1]}_{positions[2]}.jpg'    
    capture_frame(filename, directory)

    # choose next platform positions
    next_positions = get_next_positions(restricted_map, positions, travel_direction)








