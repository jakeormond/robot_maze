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
from time import sleep

def get_next_positions(platform_map, prev_positions, direction):

    n_pos = len(prev_positions)

    # get the number of rows and columns in the restricted map
    n_rows = platform_map.shape[0]
    n_cols = platform_map.shape[1]

    # find the rows and col where the elements in prev_positions are located
    rows = np.where(np.isin(platform_map, prev_positions))[0]
    col = np.where(platform_map == prev_positions[0])[1][0]
    
    # if robot is on the last row and last column, stop
    if rows[-1] == n_rows-2:
        if direction == 'right' and col == n_cols-1 or \
            direction == 'left' and col == 0:
            
            return None, None
    
    # if robot on last column, move to the next set of rows and change direction.
    # Note that if robots are moving to the final set of rows, 
    # not all 3 robots will necessarily be required. 
    if direction == 'right' and col == n_cols-1 or \
        direction == 'left' and col == 0:
        
        new_rows = np.arange(rows[-1] + 2, rows[-1] + (n_pos+1)*2, 2)
        # remove any values in new_rows that are greater than n_rows-1
        new_rows = new_rows[new_rows < n_rows]

        next_positions = platform_map[new_rows, col]

        if direction == 'right':
            direction = 'left'
        else:
            direction = 'right'

        return next_positions, direction
    
    # otherwise, move the robots left or right
    # Currently, we are assuming the top corners of the map are occupied by positions,
    # and the bottom corners by NaNs.
    # if col is even, next positions will be one row down, if col is odd,
    # next positions will be one row up
    if col % 2 == 0 and direction == 'right':
        # next positions will be one col to the right, and one row down
        next_positions = platform_map[rows+1, col+1]
    elif col % 2 == 0 and direction == 'left':
        next_positions = platform_map[rows+1, col-1]
    elif col % 2 == 1 and direction == 'right':
        next_positions = platform_map[rows-1, col+1]
    else:
        next_positions = platform_map[rows-1, col-1]
    
    return next_positions, direction

if __name__ == '__main__':
    # load the platform map
    platform_map = open_map(directory=None)
    start_platform = 41
    stop_platform = 217
    extra_row = 1

    # find rows and columns to exclude (robot can't drive there because of curtains)
    restricted_map, excluded_plats = \
        restrict_map(platform_map, start_platform, stop_platform, extra_row=extra_row, directory=None)

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
        sleep(1)

        # choose next platform positions
        next_positions, travel_direction = get_next_positions(restricted_map, 
                                                positions, travel_direction)
        
        if next_positions is None:
            break

        # move robots
        








