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

    def shortest_path(self): # will return a list of paths (i.e. a list of lists)
        # from the map, we need to find the 2 sets of 3 axes through the start 
        # end positions.
        shortest_paths = find_shortest_paths(self.start, self.end, self.map)


        # now, we need to find the intersection of the axes
        # we will do this by finding the intersection of the axes through the
        # start position with the axes through the end position

        
        
        # first, find the indices of the start and end positions in the map
        pos_ind = {}
        pos_ind['start'] = np.argwhere(self.map == self.start)
        pos_ind['end'] = np.argwhere(self.map == self.end)

        n_rows, n_cols = self.map.shape

        #
    


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

def find_axes_intersection(position1, position2, map):

    axes1 = get_axes(position1, map)
    axes2 = get_axes(position2, map)

    # axes1 and axes2 are dictionaries with keys 'vert', 'nw', and 'ne'
    # and values of lists of positions
    # find the intersections of the various axes
    intersects = {} 
    paths = {}
    for key in axes1.keys():
        intersects[key] = {}
        paths[key] = {}
        for key2 in axes2.keys():
            intersects[key][key2] = np.intersect1d(axes1[key], axes2[key2])

            if len(intersects[key][key2]) == 0:
                intersects[key][key2] = None
                paths[key][key2] = None
                
            else:
                # find position1 index in axes1[key]
                ind1a = axes1[key].index(position1)
                # find intersect index in axes1[key]
                intersects[key][key2] = intersects[key][key2][0]
                ind1b = axes1[key].index(intersects[key][key2]) 

                if ind1a > ind1b:
                    ind1a, ind1b = ind1b, ind1a
                    path_part1 = axes1[key][ind1a:ind1b+1]
                    # reverse path_part1
                    path_part1 = path_part1[::-1]
                else:
                    path_part1 = axes1[key][ind1a:ind1b]

                # position 2
                print("Key: {key}, Key2: {key2}".format(key=key, key2=key2))
                ind2a = axes2[key2].index(intersects[key][key2])             
                ind2b = axes2[key2].index(position2)
                path_part2 = axes2[key2][ind2a+1:ind2b]

                # concatenate lists
                paths[key][key2] = path_part1 + path_part2 

    return paths, intersects

