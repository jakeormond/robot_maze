'''
This code allows all platform positions to be captured and saved as jpeg images.
Later, these jpegs will be used to determine the platform positions in pixels;
this information is required for dynamic cropping of the video feed during 
data collection.
Currently, the code assumes that the top corners of the maze are occupied by
platform positions, and the bottom corners are occupied by NaNs; this can be
fixed later if necessary by adding in an intial up_down_direction variable 
(telling the robots if they initially need to move up and to the side, or 
down and to the side).
'''
import numpy as np
from honeycomb_task.configurations import read_yaml
from honeycomb_task.robot_class import Robot, Robots
from honeycomb_task.platform_map import Map
from frame_capture import capture_frame
from honeycomb_task.create_path import Paths
# from send_over_socket import send_over_sockets_threads
from honeycomb_task.send_over_socket import send_over_sockets_serial
from tkinter import filedialog
from time import sleep

def get_next_positions(platform_map, prev_positions, lr_direction):

    n_pos = len(prev_positions)

    # get the number of rows and columns in the restricted map
    n_rows = platform_map.shape[0]
    n_cols = platform_map.shape[1]

    # find the rows and col where the elements in prev_positions are located
    rows = np.where(np.isin(platform_map, prev_positions))[0]
    col = np.where(platform_map == prev_positions[0])[1][0]
    
    # if robot is on the last row and last column, stop
    if rows[-1] == n_rows-2:
        if lr_direction == 'right' and col == n_cols-1 or \
            lr_direction == 'left' and col == 0:
            
            return None, None, None
    
    # if robot on last column, move to the next set of rows and change direction.
    # Note that if robots are moving to the final set of rows, 
    # not all 3 robots will necessarily be required. 
    if lr_direction == 'right' and col == n_cols-1 or \
        lr_direction == 'left' and col == 0:
        
        new_rows = np.arange(rows[-1] + 2, rows[-1] + (n_pos+1)*2, 2)
        # remove any values in new_rows that are greater than n_rows-1
        new_rows = new_rows[new_rows < n_rows]

        next_positions = platform_map[new_rows, col]

        if lr_direction == 'right':
            lr_direction = 'left'
        else:
            lr_direction = 'right'

        order = 'reverse'

        return next_positions, lr_direction, order
    
    # otherwise, move the robots left or right
    # Currently, we are assuming the top corners of the map are occupied by positions,
    # and the bottom corners by NaNs.
    # if col is even, next positions will be one row down, if col is odd,
    # next positions will be one row up
    if col % 2 == 0 and lr_direction == 'right':
        # next positions will be one col to the right, and one row down
        next_positions = platform_map[rows+1, col+1]
        order = 'reverse'

    elif col % 2 == 0 and lr_direction == 'left':
        next_positions = platform_map[rows+1, col-1]
        order = 'reverse'

    elif col % 2 == 1 and lr_direction == 'right':
        next_positions = platform_map[rows-1, col+1]
        order = 'ascending'

    else:
        next_positions = platform_map[rows-1, col-1]
        order = 'ascending'

    
    return next_positions, lr_direction, order

if __name__ == '__main__':
    # load the platform map
    directory = 'D:/testFolder/pico_robots/map'
    # platform_map = open_map('platform_map', directory)
    map = Map(directory=directory)
    # start_platform = 41
    stop_platform = 212
    # extra_row = 1

    # find rows and columns to exclude (robot can't drive there because of curtains)
    # restricted_map, excluded_plats = \
    #    restrict_map(platform_map, start_platform, \
    #                 stop_platform, extra_row=extra_row)

    # get the number of rows and columns in the restricted map
    n_rows = map.restricted_map.shape[0]
    n_cols = map.restricted_map.shape[1]

    # lr_direction = 'right' # travel direction switches to 'left' when the robots reach the right side of the maze
    lr_direction = 'left' # travel direction switches to 'left' when the robots reach the right side of the maze

    # start_pos is a 3 element vector taken using current_rows and current_col as indices into platform_map
    # start_pos = map.restricted_map[[0, 2, 4], 0].astype(int)
    # start_pos = np.array([160, 179, 198])
    start_pos = np.array([213])
    print('start positions: ', start_pos)
    # orientations is a 3 element vector of repeating values
    # orientations = np.array([30, 30, 30])
    orientations = np.array([240])
    print('orientations: ', orientations)

    # create the robot instances
    # yaml_dir = '/media/jake/LaCie/robot_maze_workspace'
    yaml_dir = 'D:/testFolder/pico_robots/yaml'
    # robot_init = read_yaml(yaml_dir)
    # robots = Robots.from_yaml(yaml_dir, positions=start_pos, \
    #                          orientations=orientations)

    robots = Robots.from_yaml(yaml_dir, positions=start_pos, \
                             orientations=orientations, robot_ids = [3])
    robot_list = []
    for key in robots.members:
        robots.members[key].state = 'moving'
        robot_list.append(key)
    
    n_robots = len(robot_list)

    # select directory for saving images
    # directory = filedialog.askdirectory()
    directory = 'D:/testFolder/pico_robots/platform_images'

    # loop through the groups of platform positions, capturing images at each position
    while True:
        # capture image
        positions = robots.get_positions()
        filename = f'platforms_' 
        for p in positions:
            filename += f'{p}_'
        filename = filename[:-1] + '.jpg' 
        capture_frame(filename, directory)
        sleep(1)

        # choose next platform positions
        next_positions, lr_direction, order = get_next_positions(map.restricted_map, 
                                                positions, lr_direction)
        
        if next_positions is None: # we have reached the end of the maze
            break

        # assing next positions to robots
        # first, check if the list of next positions is shorter than the list of robots
        while len(next_positions) < n_robots:
            # if so, set first robot to stationary and remove it from the list
            robots.members[robot_list[0]].state = 'stationary'
            robot_list.pop(0)
            n_robots = len(robot_list)
        robots = robots.get_moving_robots()

        # get the next paths
        paths = Paths(robots, map, next_positions=next_positions)

        # send commands to robots
        if order == 'ascending':
            ordered_list = robot_list
        else:
            ordered_list = robot_list[::-1]
            
        send_over_sockets_serial(robots, paths, ordered_list)
                
        # assign next positions and orientations to robots
        for r in range(n_robots):
            robots.members[robot_list[r]].set_new_position(int(next_positions[r]))
            robots.members[robot_list[r]].set_new_orientation(paths.final_orientations[robot_list[r]])
        
        







