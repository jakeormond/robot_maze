'''
Defines a class that creates a path for the robot to follow, given a start
and end position.
It requires methods to create paths given certain constraints, such as
the shortest path, a path that avoids other robots or obstacles, etc.
'''
import numpy as np
import copy
import platform_map as pm
from platform_map import Map
import platform_map as mp  

# CreatePath should take a start and end position, and optionally a 
# list of positions to avoid
class CreatePath:
    def __init__(self, platform_map, start, end, avoid=None):
        self.map = map
        self.start = start
        self.end = end
        self.avoid = avoid


def get_starting_positions(robots, map):
    ''' the starting positions of the next path are determined by
    the initial positions of the robots. The 3 robots can adopt 
    5 configurations based on the shape of the group (i.e. line, 
    triangle or boomerang) and the position of the stationary robot
    within the group. The 5 configurations are: 1) line_end_stat, 
    2) line_mid_stat, 3) triangle, 4) boomerang_end_stat,
    5) boomerang_mid_stat. Note that at present, the code doesn't 
    distinguish configurations 1 and 2. 
    '''
    # first, identify shape
    positions = robots.get_positions()
    direction, common_axis = map.get_common_axis(robots)
    if direction is not None:
        shape = 'line'
    else:
        longest_dist = 0
        for i in range(len(positions)-1):
            for i2 in range(i+1, len(positions)):
                pos_dist = map.find_shortest_distance(positions[i], positions[i2])
                if pos_dist > longest_dist:
                    longest_dist = pos_dist
        
        if longest_dist == 1:
            shape = 'triangle'

        else:
            shape = 'boomerang'
    
    # separate stationary robot from moving robots
    stat_robot = robots.get_stat_robot()        
    moving_robots = robots.get_moving_robots()
    
    
    # now, identify position of stay put robot if shape == boomerang
    stay_put_robot = None
    initial_positions = {}
    if shape == 'boomerang':
            # get distance from each moving robot to the stat robot
            for key, r in moving_robots.items():
                pos_dist = map.find_shortest_distance(stat_robot.position,
                                                       r.position)
                if pos_dist == 2:
                    stay_put_robot = moving_robots[key]
                    initial_positions[key] = np.array([stay_put_robot.position])
                    del moving_robots[key]
                    break

    # get initial positions based on exact configuration 
    
    if shape == 'line' or shape == 'triangle' or \
        (shape == 'boomerang' and stay_put_robot == None):
        # all robots can move at +/- 120 or 180 deg to 
        # stationary robot
        directions = [-120, 120, 180]
        for key, r in moving_robots.items():
            initial_positions[key] = []

            _, dir_to_stat = map.get_direction_from_to(r.position, 
                                            stat_robot.position)
            
            for d in directions:
                new_dir = Map.add_to_dir(dir_to_stat, d)
                initial_positions[key].append(map.new_position_from_direction(\
                    r.position, new_dir, 1))
                
            initial_positions[key] = np.sort(initial_positions[key])
    
    else: # shape is boomerang and there is a stay put robot
        # the moving robot can only move to a single position which is at 
        # +/-120 deg to both the stationary robot and the stay put robot
        moving_robot_name = list(moving_robots.keys())[0]
        moving_robot = moving_robots[moving_robot_name]
        _, stat_direction = map.get_direction_from_to(moving_robot.position, 
                                                   stat_robot.position)
        _, stay_direction = map.get_direction_from_to(moving_robot.position, 
                                                   stay_put_robot.position)
        
        poss_pos_stat = []
        poss_pos_stay = []
        
        directions = [-120, 120]
        for d in directions:
            new_stat_direction = Map.add_to_dir(stat_direction, d) 
            poss_pos_stat.append(map.new_position_from_direction(\
                moving_robot.position, new_stat_direction, 1))
            
            new_stay_direction = Map.add_to_dir(stay_direction, d) 
            poss_pos_stay.append(map.new_position_from_direction(\
                moving_robot.position, new_stay_direction, 1))

        
        initial_positions[moving_robot_name] = \
            np.intersect1d(poss_pos_stat, poss_pos_stay)

    # reorder initial_positions if robot2 key is before robot1 key or 
    # robot 3 key is before robot1 or robot2 key. Unnecessary, but it 
    # seem them out of order brings out some ocd. 
    keys = list(initial_positions.keys())
    if robots.members[keys[0]].id > robots.members[keys[1]].id:
        temp_init_pos = initial_positions[keys[0]]
        del initial_positions[keys[0]]
        initial_positions[keys[0]] = temp_init_pos
       
    return initial_positions
              
         
def get_all_paths(robots, next_plats, map):
    ''' determines the paths the moving robot can take to reach
    the required position adjacent to the stationary robot'''

    # first, verify that next platforms are adjacent to the stationary robot
    stat_robot = robots.get_stat_robot()
    # get stationary robot's first order ring
    stat_robot_ring = map.get_ring_around_position(stat_robot.position, 1)
    # verify that next_plats are in stat_robot_ring
    for p in next_plats:
        if p not in stat_robot_ring:
            raise ValueError(f'Next platform {p} is not adjacent to the stationary robot.')
   
    # setermine if all robots are on the same axis, and if so,
    # if the stationary robot lies at the end of the line of robots, as this 
    # is a special case where the opposited robot will need to move to the 
    # stationary robot's 3rd order ring
    moving_robots = robots.get_moving_robots()
    # get the starting positions of the next paths
    initial_positions = get_starting_positions(robots, map)

    # the robots will travel around the stationary robots 2nd order ring
    main_ring = map.get_ring_around_position(stat_robot.position, 2)

    # get the the first order rings around each of the next_plats
    targets = {}
    for p in next_plats:
        next_plats_rings = map.get_ring_around_position(p, 1)
        # the targets are the positions included in both main_ring
        # and next_plats_rings
        targets[p] = np.intersect1d(main_ring, next_plats_rings)

    # each initial position represents two possible paths,
    # one clockwise and one anticlockwise, to each new position
    directions = ['clockwise', 'anticlockwise']
    paths = {}
    for key, r in moving_robots.items():      
        paths[key] = {}
        for p2 in next_plats:
            paths[key][f'to_plat{p2}'] = {}
            for p in initial_positions[key]:  
                paths[key][f'to_plat{p2}'][f'from_plat{p}'] = {}        
                for d in directions:
                    paths[key][f'to_plat{p2}'][f'from_plat{p}'][d] = {}

                    proto_path = copy.deepcopy(main_ring)
                    # concatenate proto_path with itself to make it easier to
                    # find the shortest path
                    proto_path = proto_path + proto_path

                    if d == 'anticlockwise':
                        proto_path = proto_path[::-1]

                    # find target positions in proto_path
                    target_ind = np.where(np.isin(proto_path, targets[p2]))[0]


                    # if p is not in protopath, then find where its first
                    # order ring intesects it
                    common_vals = None
                    if p not in proto_path:
                        # find common values between main_ring
                        # and p's first order ring
                        common_vals = np.intersect1d(main_ring,
                                map.get_ring_around_position(p, 1))
                        
                        # find where common_vals intersect proto_path
                        start_ind = np.where(np.isin(proto_path, common_vals))[0]

                        # remove target_ind values that are less than minimum start_ind value.
                        target_ind = target_ind[target_ind >= np.min(start_ind)]

                        # remove start_ind values that are greater than maximum target_ind value.
                        start_ind = start_ind[start_ind <= np.max(target_ind)]

                        min_length = None
                        final_start_ind = None
                        final_target_ind = None
                        for t in target_ind:
                            for s in start_ind:
                                path_length = t - s
                                if path_length >= 0 and (min_length is None or path_length < min_length):
                                    min_length = path_length
                                    final_start_ind = s
                                    final_target_ind = t

                        path = [p] + proto_path[final_start_ind:final_target_ind+1]             
                
                    else:
                        if p in targets[p2]:
                            path = [p]
                        else:
                            start_ind = np.where(proto_path == p)[0][0]
                            # find the start_ind value and the target_ind value that when 
                            # start_ind is subtracted from target_ind produces the smallest
                            # positive value
                            diff = target_ind - start_ind
                            # find the smallest positive value in diff
                            diff = diff[diff > 0]
                            diff = np.min(diff)
                            last_ind = start_ind + diff

                            path = proto_path[start_ind:last_ind+1]
                    
                    paths[key][f'to_plat{p2}'][f'from_plat{p}'][d] = path

    return paths

def select_optimal_paths(paths, robots, next_plats, map):
    ''' selects the optimal paths from the set of all paths. The rules are 
    1) the paths can't intersect (if robots moving in opposite directions), 
    2) can't start or finish on the same platform or occupy the same position
    at the same time step, 3) and should have the shortest possible length, 
    measured as the length of the longer of the two paths. 
    '''
    stat_robot = robots.get_stat_robot()
    moving_robots = robots.get_moving_robots()
    moving_robot_ids = list(moving_robots.keys())
    directions = 'clockwise', 'anticlockwise'

    # loop through every combination of robot1_to_plat1 and robot2_to_plat2 paths, 
    # and every combination of robot1_to_plat2 and robto2_to_plat1 paths and
    # find the shortest path that satisfies the rules.
    optimal_paths = {}

    shortest_path_length = None
    longest_path_length = None
    path_directions = [None, None]
    
    for p in next_plats: # robot1's target
        # p2 is the other entry in next_plats
        p2 = next_plats[0] if p == next_plats[1] else next_plats[1]

        # get all paths from paths[moving_robot_ids[0]][f'to_plat{p}'] 
        paths1 = paths[moving_robot_ids[0]][f'to_plat{p}']
        paths2 = paths[moving_robot_ids[1]][f'to_plat{p2}']

        

        for path1_both_dir in paths1.values():
            for d in directions:
                path1 = path1_both_dir[d]

                for path2_both_dir in paths2.values():
                    for d2 in directions:
                        path2 = path2_both_dir[d2]

                        # check path compatibility 
                        # 1) paths can't intersect if robots moving in opposite directions
                        if d != d2 and len(np.intersect1d(path1, path2)) > 0:
                            continue

                        # 2) can't start or finish on the same platform or occupy the same position
                        # at the same time step
                        if path1[0] == path2[0] or path1[-1] == path2[-1]:
                             continue
                        
                        min_path_length = np.min([len(path1), len(path2)])
                        max_path_length = np.max([len(path1), len(path2)])
                        identical_step = False
                        for s in range(min_path_length):
                            if path1[s] == path2[s]:
                                identical_step = True                                
                                break
                        if identical_step:
                            continue

                        # 3) should have the shortest possible length
                        path1_length = len(path1)
                        path2_length = len(path2)
                        
                        if (shortest_path_length == None and longest_path_length == None) or \
                            (max_path_length < longest_path_length) or \
                                (max_path_length == max_path_length and \
                                    min_path_length < shortest_path_length) or \
                                        (d != d2 and path_directions[0] == path_directions[1]):
                            
                            shortest_path_length = min_path_length
                            longest_path_length = max_path_length

                            path_directions[0] = d
                            path_directions[1] = d2

                            optimal_paths[moving_robot_ids[0]] = path1 + [p]
                            optimal_paths[moving_robot_ids[1]] = path2 + [p2]
        
    return optimal_paths

if __name__ == '__main__':
    import platform_map
    directory = '/media/jake/LaCie/robot_maze_workspace'
    # directory = 'C:/Users/Jake/Desktop/map_of_platforms'
    # map = platform_map.open_map(map='restricted_map', directory=directory)
    map = Map(directory=directory)
    # paths = find_shortest_paths(91, 72, map)

    import robot_class
    robot1 = robot_class.Robot(1, '192.100.0.101', 1025, 63, 0, 'moving', map)
    # rings = get_rings(robot1, map)
    robot2 = robot_class.Robot(2, '192.100.0.102', 1026, 53, 0, 'moving', map)
    # robot3 = robot_class.Robot(3, '192.100.0.103', 1027, 73, 0, 'moving', map)
    robot3 = robot_class.Robot(3, '192.100.0.103', 1027, 43, 0, 'stationary', map)
    # robot3 = robot_class.Robot(3, '192.100.0.103', 1027, 82, 0, 'stationary', map)

    robots = robot_class.Robots()
    robots.add_robots([robot1, robot2, robot3])

    next_plats = [33, 24]    
    # initial_positions = get_starting_positions(robots, map)
    paths = get_all_paths(robots, next_plats, map)
    optimal_paths = select_optimal_paths(paths, robots, next_plats, map)
    print(optimal_paths)