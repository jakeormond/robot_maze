'''
Defines a class that creates a path for the robot to follow, given a start
and end position.
It requires methods to create paths given certain constraints, such as
the shortest path, a path that avoids other robots or obstacles, etc.
'''
import numpy as np
import copy

# CreatePath should take a start and end position, and optionally a 
# list of positions to avoid
class CreatePath:
    def __init__(self, platform_map, start, end, avoid=None):
        self.map = map
        self.start = start
        self.end = end
        self.avoid = avoid

    def shortest_path(self): # will return a dictionary of paths, with keys
        # indicating the direction of the intersecting axes through each of the
        # two positions 
        return find_shortest_paths(self.start, self.end, self.map)

        

def get_axes(position, map):

    n_rows, n_cols = map.shape

    ind = np.argwhere(map == position)
    ind = ind[0]
    
    # get all 3 axes through the start and end positions
    vert_axis = map[:, ind[1]]; # vertical axis
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
        nw_axis.insert(0, map[ind_nw[0], ind_nw[1]])
    ind_nw = copy.deepcopy(ind[:])
    while True:
        ind_nw = ind_nw + 1
        if ind_nw[0] == n_rows or ind_nw[1] == n_cols:
            break
        nw_axis.append(map[ind_nw[0], ind_nw[1]])

    ne_axis =[position]
    ind_ne = copy.deepcopy(ind[:])
    while True:
        ind_ne[0] = ind_ne[0] + 1
        ind_ne[1] = ind_ne[1] - 1
        if ind_ne[0] == n_rows or ind_ne[1] < 0:
            break        
        # append value to the beginning of the list     
        ne_axis.insert(0, map[ind_ne[0], ind_ne[1]])
    ind_ne = copy.deepcopy(ind[:])
    while True:
        ind_ne[0] = ind_ne[0] - 1
        ind_ne[1] = ind_ne[1] + 1
        if ind_ne[0] < 0 or ind_ne[1] == n_cols:
            break
        ne_axis.append(map[ind_ne[0], ind_ne[1]])

    axes = {}
    axes['vert'] = vert_axis
    axes['nw'] = nw_axis
    axes['ne'] = ne_axis
    return axes

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
                path_part2 = axes2[key2][ind2a+1:ind2b+1]

                path_temp = path_part1 + path_part2   
                path_length = len(path_temp)

                # concatenate lists              
                if path_length < min_length:
                    min_length = path_length

                    paths[key] = {}
                    paths[key][key2] = path_temp
                    # remove all other paths
                    for key3 in paths[key].keys():
                        if key3 != key2:
                            del paths[key][key3]
                    

                elif path_length == min_length:
                    # if paths[key] already exists, add key2 to it, otherwise create it
                    if key in paths.keys():
                        paths[key][key2] = path_temp
                    else:
                        paths[key] = {}
                        paths[key][key2] = path_temp

    return paths

if __name__ == '__main__':
    import platform_map
    map = platform_map.open_map(map='restricted_map', directory= 
                                '/media/jake/LaCie/robot_maze_workspace')
    paths = find_shortest_paths(91, 131, map)