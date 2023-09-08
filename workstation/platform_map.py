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
import copy

# map definition
class Map:
    def __init__(self, n_rows=None, n_cols=None, directory=None):
        # if n_rows is not None:
        if n_rows is not None:
            self.platform_map = generate_map(n_rows, n_cols)
            self.restricted_map = None
            self.excluded_plats = None
        
        else:
            self.open_map(directory=directory)

    def restrict_map(self, start_platform, stop_platform, extra_row=0):
        self.restricted_map, self.excluded_plats = \
            restrict_map(self.platform_map, start_platform, stop_platform, extra_row)

    def save_map(self, directory=None):
        map_types = ['platform_map', 'restricted_map']
        for map_type in map_types:
            if map_type == 'platform_map':
                directory = save_map(map_type, self.platform_map, directory)
            else:
                if self.restricted_map is None:
                    print('Restricted map has not been generated yet.')
                else:
                    save_map(map_type, self.restricted_map, directory)
    
    def open_map(self, directory=None):
        if directory == None:
            # ask user to select directory from gui
            root = tk.Tk()
            root.withdraw()
            directory = filedialog.askdirectory()

        self.platform_map = open_map(map_type='platform_map', directory=directory)
        
        # determine if file restricted_map.csv exists in directory
        restricted_map_filepath = os.path.join(directory, 'restricted_map.csv')
        if os.path.isfile(restricted_map_filepath):
            self.restricted_map = open_map(map_type='restricted_map', directory=directory)

            # generate excluded_plats
            self.excluded_plats = []
            for i in range(self.platform_map.shape[0]):
                for j in range(self.platform_map.shape[1]):
                    # if platform_map[i,j] is not nan and is not contained in restricted_map, then append
                    if not np.isnan(self.platform_map[i,j]) and \
                        self.platform_map[i,j] not in self.restricted_map:
                        self.excluded_plats.append(self.platform_map[i,j])
        else:
            print('Restricted map has not been generated yet.')

    def get_indices_of_postion(self, position):
        return np.argwhere(self.platform_map == position)[0]
    
    def get_axes(self, position):
        return get_axes(position, self)
    
    def get_common_axis(self, robots):
        ''' determines what axes the robots have in common.'''
        # find if all keys in axes are nan, if so, then all robots are on different axes
        # and there is no common axis
        for r in robots.members.keys():
            axes = self.get_axes(robots.members[r].position)
            if r == 'robot1':
                common_axes = axes
            else:
                for key in axes.keys():
                    if axes[key] == common_axes[key]:
                        continue
                    else:
                        common_axes[key] = np.nan

        # if any common_axes entry is not nan, return it
        for key in common_axes.keys():
            if not np.isnan(common_axes[key]).all():
                return key, common_axes[key]
        return None, None

    def straight_path(self, position1, position2):
        return straight_path(position1, position2, self)
    
    def get_ring_around_position(self, position, ring_order):
        return get_ring(position, self, ring_order)

    def get_rings_around_position(self, position, ring_order=3):
        return get_rings(position, self, ring_order)

    def find_shortest_distance(self, position1, position2): 
        '''Simply find the order of the ring around position1
            that contains position2, and return the ring order'''

        if position1 == position2:
            return 0
            
        distance = 1
        while True:
            ring = self.get_ring_around_position(position1, distance)
            if ring is None:
                return None
            if position2 in ring:
                return distance
            distance += 1    
    
    def get_direction_from_to(self, position1, position2):
        # get the direction from position1 to position2
        # returns 'vert', 'nw', or 'ne'. MUST BE ON SAME AXIS!
        axes1 = self.get_axes(position1)
        axes2 = self.get_axes(position2)

        for key in axes1.keys():
            if position2 in axes1[key]:
                # get indices of position1 and position2 in axes1[key]
                ind1 = axes1[key].index(position1)
                ind2 = axes1[key].index(position2)

                if ind1 > ind2:
                    if key == 'vert':
                        return 'north', 0
                    elif key == 'ne':
                        return 'northeast', 60
                    else:
                        return 'northwest', 300
                else:
                    if key == 'vert':
                        return 'south', 180
                    elif key == 'ne':
                        return 'southwest', 240
                    else:
                        return 'southeast', 120
                
        return None, None
    
    def new_position_from_direction(self, position, direction, distance):
        axes = self.get_axes(position)
        if direction == 'north' or direction == 0:
            axis = axes['vert']
            # reverse axis
            axis = axis[::-1]
        elif direction == 'south' or direction == 180:
            axis = axes['vert']
        elif direction == 'northeast' or direction == 60:
            axis = axes['ne']
            # reverse axis
            axis = axis[::-1]
        elif direction == 'southwest' or direction == 240:
            axis = axes['ne']
        elif direction == 'northwest' or direction == 300:
            axis = axes['nw']
            # reverse axis
            axis = axis[::-1]
        else: # direction == 'southeast':
            axis = axes['nw']

        ind = axis.index(position)
        return axis[ind + distance]
    
    @staticmethod
    def add_to_dir(direction, angle):
        new_angle = direction + angle
        if new_angle >= 360:
            new_angle = new_angle - 360 
        elif new_angle < 0:
            new_angle = new_angle + 360
        return new_angle



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

    return platform_map

def get_axes(position, map):

    n_rows, n_cols = map.platform_map.shape

    ind = np.argwhere(map.platform_map == position)
    ind = ind[0]
    
    # get all 3 axes through the start and end positions
    vert_axis = map.platform_map[:, ind[1]]; # vertical axis
    vert_axis = vert_axis[~np.isnan(vert_axis)] # remove nan values
    # convert to list
    vert_axis = vert_axis.tolist()

    nw_axis =[position]
    ind_nw = copy.deepcopy(ind[:])
    while True:
        ind_nw = ind_nw - 1
        if ind_nw[0] < 0 or ind_nw[1] < 0:
            break        
        # append value to the beginning of the list     
        nw_axis.insert(0, map.platform_map[ind_nw[0], ind_nw[1]])
    ind_nw = copy.deepcopy(ind[:])
    while True:
        ind_nw = ind_nw + 1
        if ind_nw[0] == n_rows or ind_nw[1] == n_cols:
            break
        nw_axis.append(map.platform_map[ind_nw[0], ind_nw[1]])

    ne_axis =[position]
    ind_ne = copy.deepcopy(ind[:])
    while True:
        ind_ne[0] = ind_ne[0] - 1
        ind_ne[1] = ind_ne[1] + 1
        if ind_ne[0] < 0 or ind_ne[1] == n_cols:
            break        
        # append value to the beginning of the list     
        ne_axis.insert(0, map.platform_map[ind_ne[0], ind_ne[1]])
   
    ind_ne = copy.deepcopy(ind[:])
    while True:
        ind_ne[0] = ind_ne[0] + 1
        ind_ne[1] = ind_ne[1] - 1
        if ind_ne[0] == n_rows or ind_ne[1] < 0:
            break     
        ne_axis.append(map.platform_map[ind_ne[0], ind_ne[1]])  

    axes = {}
    axes['vert'] = vert_axis
    axes['nw'] = nw_axis
    axes['ne'] = ne_axis
    
    return axes

def straight_path(position1, position2, map):
    axes = map.get_axes(position1)
    
    ind1 = map.get_indices_of_postion(position1)
    ind2 = map.get_indices_of_postion(position2)

    # either positions are on vertical axis, in which case their column indices are identical
    if ind1[1] == ind2[1]:
        # on vertical axis
        axis = axes['vert']
    
    elif np.abs(ind1[0] - ind2[0]) != np.abs(ind1[1] - ind2[1]): 
        # if the row and column indices are not equidistant, then there is no straight path
        return None
    
    else:
        if ind1[0] - ind2[0] == ind1[1] - ind2[1]:
            # on northwest axis
            axis = axes['nw']
        else:
            # on northeast axis
            axis = axes['ne']
    
    # find the indices of position1 and position2 in axis
    ind1 = axis.index(position1)
    ind2 = axis.index(position2)

    if ind1 > ind2:
        # reverse axis
        path = axis[ind2:ind1+1]
        path = path[::-1]
    else:
        path = axis[ind1:ind2+1]
    
    return path

def find_shortest_paths(position1, position2, map):

    axes1 = get_axes(position1, map)
    axes2 = get_axes(position2, map)

    # axes1 and axes2 are dictionaries with keys 'vert', 'nw', and 'ne'
    # and values of lists of positions
    # find the intersections of the various axes
    # first, find if they have any identical axes, check if 
    # axis1[key] == axis2[key] for all keys
    paths = {}
    for key in axes1.keys():
        if axes1[key] == axes2[key]:
            # if they are identical, then we have found the shortest path
            ind1a = axes1[key].index(position1)
            ind1b = axes1[key].index(position2)

            if ind1a > ind1b:
                ind1a, ind1b = ind1b, ind1a
                paths[key] = axes1[key][ind1a:ind1b+1]
                # reverse paths[key]
                paths[key] = paths[key][::-1]
            else:
                paths[key] = axes1[key][ind1a:ind1b+1]
            return paths
    
    min_length = np.inf
    for key in axes1.keys():
        for key2 in axes2.keys():
            intersects = np.intersect1d(axes1[key], axes2[key2])

            if len(intersects) == 0:
                continue
                
            else:
                # find position1 index in axes1[key]
                ind1a = axes1[key].index(position1)
                # find intersect index in axes1[key]
                intersects = intersects[0]
                ind1b = axes1[key].index(intersects) 

                if ind1a > ind1b:
                    ind1a, ind1b = ind1b, ind1a
                    path_part1 = axes1[key][ind1a:ind1b+1]
                    # reverse path_part1
                    path_part1 = path_part1[::-1]
                else:
                    path_part1 = axes1[key][ind1a:ind1b+1]

                # position 2
                ind2a = axes2[key2].index(intersects)
                ind2b = axes2[key2].index(position2)


                if ind2a > ind2b:
                    ind2a, ind2b = ind2b, ind2a
                    path_part2 = axes2[key2][ind2a:ind2b+1]
                    # reverse path_part2
                    path_part2 = path_part2[::-1]
                else:
                     path_part2 = axes2[key2][ind2a:ind2b+1]

                path_temp = path_part1 + path_part2[1:]   
                path_length = len(path_temp)

                # concatenate lists              
                if path_length < min_length:
                    min_length = path_length

                    paths[key] = {}
                    paths[key][key2] = path_temp
                    # remove all other paths in paths[key]
                    for key3 in paths[key].keys():
                        if key3 != key2:
                            del paths[key][key3]
                    # remove all other paths in paths
                    keys = list(paths.keys())
                    for key3 in keys:
                        if key3 != key:
                            del paths[key3]
                    

                elif path_length == min_length:
                    # if paths[key] already exists, add key2 to it, otherwise create it
                    if key in paths.keys():
                        paths[key][key2] = path_temp
                    else:
                        paths[key] = {}
                        paths[key][key2] = path_temp

    return paths

def get_ring(position, map, ring_order):
    axes = get_axes(position, map)
    axes_names = ['vert', 'ne', 'nw']
    vertices = [np.nan] * 6

    for a in axes_names:
        pos_ind = axes[a].index(position)

        if a == 'vert':
            vertex_ind = [0,3]
        elif a == 'ne':
            vertex_ind = [1,4]
        else:
            vertex_ind = [5,2]
    
        if pos_ind - ring_order < 0:
            vertices[vertex_ind[0]] = np.nan
        else:
            vertices[vertex_ind[0]] = axes[a][pos_ind - ring_order]

        if pos_ind + ring_order >= len(axes[a]):
            vertices[vertex_ind[1]] = np.nan
        else:
            vertices[vertex_ind[1]] = axes[a][pos_ind + ring_order]

    if ring_order == 1:
        return vertices
    
    ring = []
    for i in range(len(vertices)):
        if i == len(vertices) - 1:
            i2 = 0
        else:
            i2 = i + 1

        # if vertices[f'ring{o+1}'][i] is nan, then skip
        if np.isnan(vertices[i]) or np.isnan(vertices[i2]):
            continue

        ring_section = map.straight_path(vertices[i], vertices[i2])
        
        # append ring_section to rings[f'ring{o+1}']
        ring = ring + ring_section[:-1]

    return ring

def get_rings(position, map, ring_order=3):
    '''  note that currently, if the position is too close to the maze edge,
    the 3rd order ring will have some gaps; currently, this shouldn't 
    cause any problems. 
    '''
    rings = {}
    for r in range(1,ring_order+1):
        rings[str(r)] = map.get_ring(position, r)
    
    return rings

def find_shortest_distance(position1, position2, map):
    '''Simply find the order of the ring around position1
    that contains position2, and return the ring order'''

    if position1 == position2:
        return 0
    
    distance = 1
    while True:
        ring = map.get_ring_around_position(position1, distance)
        if ring is None:
            return None
        if position2 in ring:
            return distance
   
def open_map(map_type=None, directory=None):
    if directory is None:
        # ask user to select directory from gui
        root = tk.Tk()
        root.withdraw()
        print('Select directory containing map')
        directory = filedialog.askdirectory()
        
    if map_type is None:
        filepath = os.path.join(directory, 'platform_map.csv')
    else:
        filepath = os.path.join(directory, map_type + '.csv')
    
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


def restrict_map(platform_map, start_platform, stop_platform, extra_row=0):
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

    # save_map('restricted_map.csv', restricted_map, directory=None)
    
    return restricted_map, excluded_plats

def save_map(filename, map, directory=None):
    if directory is None:
        # ask user to select directory from gui
        root = tk.Tk()
        root.withdraw()
        directory = filedialog.askdirectory()

    filepath = os.path.join(directory, filename + '.csv')
    np.savetxt(filepath, map, delimiter=',')
    
    return directory

if __name__ == '__main__':
    directory = "/media/jake/LaCie/robot_maze_workspace"
    
    # map = Map(26, [9, 10])
    # map.restrict_map(41, 217, extra_row=1)
    
    map = Map(directory=directory)
        
    # map.save_map()
    position = 164
    print(f'indices of position {position} = {map.get_indices_of_postion(position)}')      
    
    # axes = map.get_axes(position)

    # rings = map.get_rings_around_position(position)
      
    # straight_path(166, 164, map)

    direction = map.get_direction_from_to(166, 185)