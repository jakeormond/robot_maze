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
        ind_ne[0] = ind_ne[0] - 1
        ind_ne[1] = ind_ne[1] + 1
        if ind_ne[0] < 0 or ind_ne[1] == n_cols:
            break        
        # append value to the beginning of the list     
        ne_axis.insert(0, map[ind_ne[0], ind_ne[1]])
   
    ind_ne = copy.deepcopy(ind[:])
    while True:
        ind_ne[0] = ind_ne[0] + 1
        ind_ne[1] = ind_ne[1] - 1
        if ind_ne[0] == n_rows or ind_ne[1] < 0:
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

def get_all_paths(robots, next_plats, map):
    ''' determines the paths the moving robot can take to reach
    the required position adjacent to the stationary robot'''

    # first, need to determine if all robots are on the same axis, and if so,
    # if the stationary robot lies at the end of the line of robots, as this 
    # is a special case where the opposited robot will need to move to the 
    # stationary robot's 3rd order ring
    
    axes = []
    for r in range(3):
        axes.append(get_axes(robots[f'robot{r+1}'].position, map))

        # create 2 element list of nan values
        common_axes = [np.nan] * 2
        if r != 0:
            for key in axes[r].keys():
                if axes[r][key] == axes[r-1][key]:
                    common_axes.append(key)
                    break
    if common_axes[0] == common_axes[1]: # this special condition is met
        # so robot that is in stat robots 2nd order ring will need to move to
        # the stat robot's 3rd order ring
        pass # will need to implement this later


    moving_rings = get_rings(robot, map)
    stat_rings = get_rings(stat_robot, map)

    for p in next_plats:
        final_pos_rings = get_rings(p, map)









def get_rings(robot, map):
    '''  note that currently, if the position is too close to the maze edge,
    the 3rd order ring will have some gaps; currently, this shouldn't 
    cause any problems. 
    '''
    axes = get_axes(robot.position, map)
    # axes_names = list(axes.keys())
    axes_names = ['vert', 'ne', 'nw']
    vertices = {}
    
    highest_ring_order = 3 # i.e. largest ring is 3 platforms outside current position
    for o in range(highest_ring_order):
        vertices[f'ring{o+1}'] = [np.nan] * 6

    for a in axes_names:
        pos_ind = axes[a].index(robot.position)

        if a == 'vert':
            vertex_ind = [0,3]
        elif a == 'ne':
            vertex_ind = [1,4]
        else:
            vertex_ind = [5,2]

        for o in range(highest_ring_order):
            if pos_ind - o - 1 < 0:
                vertices[f'ring{o+1}'][vertex_ind[0]] = np.nan
            else:
                vertices[f'ring{o+1}'][vertex_ind[0]] = axes[a][pos_ind-o-1]

            if pos_ind + o + 1 >= len(axes[a]):
                vertices[f'ring{o+1}'][vertex_ind[1]] = np.nan
            else:
                vertices[f'ring{o+1}'][vertex_ind[1]] = axes[a][pos_ind+o+1]

    rings = {}
    rings['ring1'] = vertices['ring1']

    for o in range(1, highest_ring_order): # need to fill in rings of order 2 and higher
        rings[f'ring{o+1}'] = []
        for i in range(len(vertices[f'ring{o+1}'])):
            if i == len(vertices[f'ring{o+1}']) - 1:
                i2 = 0
            else:
                i2 = i + 1

            # if vertices[f'ring{o+1}'][i] is nan, then skip
            if np.isnan(vertices[f'ring{o+1}'][i]) or np.isnan(vertices[f'ring{o+1}'][i2]):
                continue

            ring_section = find_shortest_paths(vertices[f'ring{o+1}'][i], 
                                               vertices[f'ring{o+1}'][i2], map)
            # convert ring_section to a list
            ring_section = list(ring_section.values())[0]

            # append ring_section to rings[f'ring{o+1}']
            rings[f'ring{o+1}'] = rings[f'ring{o+1}'] + ring_section[:-1]

    return rings

if __name__ == '__main__':
    import platform_map
    # directory = '/media/jake/LaCie/robot_maze_workspace'
    directory = 'C:/Users/Jake/Desktop/map_of_platforms'
    # map = platform_map.open_map(map='restricted_map', directory=directory)
    map = platform_map.open_map(map='platform_map', directory=directory)
    # paths = find_shortest_paths(91, 72, map)

    import robot_class
    robot1 = robot_class.Robot(1, '192.100.0.101', 1025, 43, 0)
    rings = get_rings(robot1, map)
