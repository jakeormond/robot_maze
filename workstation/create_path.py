'''
Defines a class that creates a path for the robot to follow, given a start
and end position.
It requires methods to create paths given certain constraints, such as
the shortest path, a path that avoids other robots or obstacles, etc.
'''
import numpy as np
import copy
import os
from robot_class import Robot, Robots 
import platform_map as pm
from platform_map import Map
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time


# CreatePath should take a start and end position, and optionally a 
# list of positions to avoid
class Paths:
    def __init__(self, robots, map, next_positions=None, task='task', \
                 difficulty = 'hard', choices = None, time_per_turn = 0.5, \
                    time_per_line = 1.):
        
        if task == 'task':       
            if next_positions is None:
                # pick next positions
                self.next_plats = get_next_positions(robots, map, choices, difficulty)

            else:
                self.next_plats = next_positions
                
            # get all possible paths
            self.all_paths = get_all_paths(robots, self.next_plats, map)

            # select the optimal paths
            self.optimal_paths = select_optimal_paths(self.all_paths, robots, self.next_plats, map)

        elif task == 'move_away': # the rat is at goal, so other 2 robots need to move away
            # in this case, we can just use the get_starting_positions method to get the 
            # next positions
            next_positions = get_starting_positions(robots, map)
            # this will produce multiple choices for the next platforms. We will choose based 
            # on the smallest turn angle for the moving robots
            angle_diffs = {}
            for key in next_positions.keys():
                plat_orientation = robots.members[key].orientation

                angle_diffs[key] = []
                for p in next_positions[key]:
                    _, angle = map.get_direction_from_to(robots.members[key].position, p)
                    angle_diff = angle - plat_orientation
                    if angle_diff > 180:
                        angle_diff -= 360
                    elif angle_diff < -180:
                        angle_diff += 360              

                    angle_diffs[key].append(angle_diff)
            
            # determing if the 2 robots have overlapping sets of next platforms
            keys = list(angle_diffs.keys())
            i = 0
            while i < len(next_positions[keys[0]]):
                # find index of next_positions[keys[0]] in next_positions[keys[1]]
                i2 = np.where(next_positions[keys[1]] == next_positions[keys[0]][i])[0]
                if len(i2) > 0:
                    if abs(angle_diffs[keys[0]][i]) < abs(angle_diffs[keys[1]][i2[0]]):
                        # remove next_positions[keys[1]][i2] from next_positions[keys[1]]
                        next_positions[keys[1]] = np.delete(next_positions[keys[1]], i2)
                        angle_diffs[keys[1]] = np.delete(angle_diffs[keys[1]], i2)
                    else:
                        # remove next_positions[keys[0]][i] from next_positions[keys[0]]
                        next_positions[keys[0]] = np.delete(next_positions[keys[0]], i)
                        angle_diffs[keys[0]] = np.delete(angle_diffs[keys[0]], i)
                    
                else:
                    i += 1                                    
            
            # now, we can select the next positions based on the smallest angle difference
            next_pos_list = []
            for key in next_positions.keys():
                min_ind = np.argmin(np.abs(angle_diffs[key]))
                next_pos_list.append(next_positions[key][min_ind])

            # select the optimal paths
            self.optimal_paths = get_direct_paths(robots, next_pos_list, map)

        else: # moving robots directly to next positions
            self.next_plats = next_positions
            self.optimal_paths = get_direct_paths(robots, next_positions, map)

        # get commands and timings
        self.command_strings, self.commands, self.orientations \
            = paths_to_commands(robots, self.optimal_paths, map)        
        
        # self.time_per_turn = time_per_turn

        # self.time_per_line = time_per_line
        
        # self.command_strings, self.durations, self.command_numeric, \
        #      self.final_orientations = paths_to_commands(robots, \
        #             self.optimal_paths, map, self.time_per_turn, self.time_per_line)        

    def split_off_initial_turn(self):
        initial_turns = split_off_initial_turn(self)
        return initial_turns
    
    def plot_paths(self, robots, map):
        fig_handle = plot_paths(map, robots, self.optimal_paths)
        self.fig_handle = fig_handle

    def close_paths_plot(self):
        close_paths_plot(self.fig_handle)
        self.fig_handle = None
        

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
    # separate stationary robot from moving robots
    stat_robot = robots.get_stat_robot()        
    moving_robots = robots.get_moving_robots()    
    initial_positions = {}
    # first, check if all robots at least 2 pairs of robots are 
    # adjacent to each other. They should be if the task has started,
    # but at trial start, the moving robots should be placed 1 platform
    # away from the stationary robot, and 1 platform away from each other; 
    # in that case, there current positions are the starting positions so 
    # no need to compute new ones.
    adj_bool = map.check_robots_adjacent(robots)
    if not adj_bool:
        keys = moving_robots.members.keys()
        for key in keys:
            initial_positions[key] = np.array([moving_robots.members[key].position])
       
        return initial_positions

    # if proceeding, identify shape
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
      
    # now, identify position of stay put robot if shape == boomerang
    stay_put_robot = None
    if shape == 'boomerang':
            # get distance from each moving robot to the stat robot
            for key, r in moving_robots.members.items():
                pos_dist = map.find_shortest_distance(stat_robot.position,
                                                       r.position)
                if pos_dist == 2:
                    stay_put_robot = moving_robots.members[key]
                    initial_positions[key] = np.array([stay_put_robot.position])
                    del moving_robots.members[key]
                    break

    # get initial positions based on exact configuration 
    
    if shape == 'line' or shape == 'triangle' or \
        (shape == 'boomerang' and stay_put_robot == None):
        # all robots can move at +/- 120 or 180 deg to 
        # stationary robot
        directions = [-120, 120, 180]
        for key, r in moving_robots.members.items():
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
        moving_robot_name = list(moving_robots.members.keys())[0]
        moving_robot = moving_robots.members[moving_robot_name]
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
    # robot 3 key is before robot1 or robot2 key. Unnecessary, but 
    # seeing them out of order brings out some ocd. 
    keys = list(initial_positions.keys())
    if robots.members[keys[0]].id > robots.members[keys[1]].id:
        temp_init_pos = initial_positions[keys[0]]
        del initial_positions[keys[0]]
        initial_positions[keys[0]] = temp_init_pos
       
    return initial_positions


def get_next_positions(robots, map, choices, difficulty):
    ''' identify the stationary robot, and pseudo-randomly
    pick the next two positions for the moving robots, such that 
    previous options are avoided if possible. '''

    # get stationary robot
    stat_robot = robots.get_stat_robot()
    stat_robot_pos = stat_robot.position

    # get first order ring around stationary robot
    possible_targets = np.sort(map.get_ring_around_position(stat_robot_pos, 1))
    # remove positions that are in excluded_positions
    excluded_positions = map.excluded_plats
    possible_targets = np.setdiff1d(possible_targets, excluded_positions)
    # get number of possible target pairs
    n_possible_pairs = len(possible_targets) * (len(possible_targets) - 1) / 2
    # create array containing all possible pairs
    possible_pairs = np.zeros((int(n_possible_pairs), 2))
    pair_ind = 0
    for i in range(len(possible_targets)-1):
        for i2 in range(i+1, len(possible_targets)):
            possible_pairs[pair_ind] = [possible_targets[i], possible_targets[i2]]
            pair_ind += 1
    
    # find what, if any, choices have previously been made from stat_robot_pos using 
    # the choices.data pandas dataframe
    if choices != None:

        choices.data = choices.data[choices.data['start_pos'] == stat_robot_pos]
        # extract the chosen and unchosen positions to a numpy array and remove 
        # any repeated pairs
        n_prev_pairs = 0
        if choices.data.empty == False:
            previous_pairs = choices.data[['chosen_pos', 'unchosen_pos']].to_numpy()
            previous_pairs = previous_pairs.astype(int)
            for p in range(previous_pairs.shape[0]):
                previous_pairs[p] = np.sort(previous_pairs[p])
            # remove duplicate pairs
            previous_pairs = np.unique(previous_pairs, axis=0)
            n_prev_pairs = previous_pairs.shape[0]

            if n_prev_pairs != n_possible_pairs: # remove common pairs
                for p in previous_pairs:
                    if p in possible_pairs:
                        # find row index of p in possible pairs
                        row_ind = np.where(np.all(possible_pairs == p, axis=1))[0][0]
                        # delete row from possible_pairs
                        possible_pairs = np.delete(possible_pairs, row_ind, axis=0)
    
    # randomly reorder possible_pairs
    np.random.shuffle(possible_pairs)

    # loop through the pairs, breaking if a pair satisfies the difficulty
    # criteria
    next_positions = None
    while_counter = 0
    while next_positions is None:
        for p in possible_pairs:
            # get cartesian distance from stat_robot_pos
            stat_dist = map.cartesian_distance(stat_robot_pos, map.goal_position)

            # get cartesian distance from p[0] and p[1]
            p0_dist = map.cartesian_distance(p[0], map.goal_position)
            p1_dist = map.cartesian_distance(p[1], map.goal_position)

            if difficulty == 'hard':  
                if while_counter == 0:
                    if p0_dist < stat_dist or p1_dist < stat_dist:
                        next_positions = p
                        break
                    else:
                        if p0_dist == stat_dist or p1_dist == stat_dist:
                            next_positions = p
                            break           
            
            else:
                if while_counter == 0:
                    if p0_dist < stat_dist and p1_dist < stat_dist:
                        next_positions = p
                        break
                else:
                    if p0_dist < stat_dist or p1_dist < stat_dist:
                        next_positions = p
                        break
    
    return next_positions

def get_direct_paths(robots, next_plats, map):
    # get moving robots
    moving_robots = robots.get_moving_robots()
    # verify that there are the same number of moving robots and next_plats
    if len(moving_robots.members) != len(next_plats):
        raise ValueError('Number of moving robots must equal number of next_plats')

    paths = {}
    for i, key in enumerate(moving_robots.members):
        paths[key] = map.straight_path(moving_robots.members[key].position, next_plats[i])

    return paths

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
   
    # determine if all robots are on the same axis, and if so,
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
    for key, r in moving_robots.members.items():      
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
    moving_robot_ids = list(moving_robots.members.keys())
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

def construct_paths(robots, next_plats, map):
    # get all possible paths
    all_paths = get_all_paths(robots, next_plats, map)

    # select the optimal paths
    optimal_paths = select_optimal_paths(all_paths, robots, next_plats, map)

    return optimal_paths

# def path_to_command(robot, path, map, time_per_turn, time_per_line):
def path_to_command(robot, path, map):
    ''' converts path to the robot command. The command takes
      the form of a series of turns and linear movements: 
      e.g. the command [2,1,4,2] would tell the robot to turn clockwise by
      2 lines, then move forward 1 line, then turn counter-clockwise by 4 
      (i.e. 6-2) lines, then forward 2 lines'''
    
    command = []
    directions = []

    # get starting position and direction
    start_pos = robot.position
    start_direction = robot.orientation
    
    # check if path begins with start positions; if it does, this  indicates
    # that the robot needs to wait for the other robot to move out of the way
    # (unless it is the start of the trial, but we handle this elsewhere).
    if start_pos == path[0]:
        command = [0, 0]
    else:
        path = [start_pos] + path

    # loop through each position in path
    linear_counter = 0
    prev_direction = start_direction
    for i, p in enumerate(path[:-1]):
        # get direction from current position to p
        _, direction = map.get_direction_from_to(p, path[i+1])
        directions.append(direction)

        # if direction is not the same as prev_direction, then set the linear
        # distance from the incremented linear_counter, and then calculate turn
        if direction != prev_direction and i > 0:
                command.append(linear_counter)
                linear_counter = 0
        if i == 0 or direction != prev_direction:
            turn_degrees = Map.add_to_dir(direction, -prev_direction) # calculating difference
            turn_lines = turn_degrees / 60
            command.append(turn_lines)
            prev_direction = direction
        linear_counter += 1
    
    # append final linear_counter to command
    command.append(linear_counter)    
    subcommands = [None, None, None]
    suborientations = [None, None]

    subcommands[0] = [command[0]]
    suborientations[0] = [directions[0]]
    
    if command[1] == 0:
        subcommands[1] = command[2:-1]
    else:
        subcommands[1] = command[1:-1]
        subcommands[1].insert(0,0)
    subcommands[2] = [0, command[-1]]

    if len(directions) == 1:
        suborientations[1] = [directions[0]]
    else:
        suborientations[1] = directions[1:]

    # cast command to int
    for i in range(len(subcommands)):
        subcommands[i] = [int(c) for c in subcommands[i]]

    # duration = get_command_timing(subcommands, time_per_turn = 0.5, time_per_line = 1.)

    command_string = int_to_string_command(subcommands)

    # final_orientation = direction
    # final_orientation = directions[-1]

    # return command_string, duration, subcommands, final_orientation
    return command_string, subcommands, suborientations

# def get_command_timing(command, time_per_turn = 0.5, time_per_line = 1.):

#     ''' returns the timing of the command in seconds. The timing is based on the estimated 
#     cumulative time it takes the robots to execute the movements in the command. 
#     In the future, this should be replaced with a more accurate timing based on empirical
#     tests of the robots '''

#     # determine how many lists are in command
#     n_lists = len(command)

#     # calculate duration of each sub-command
#     duration = [0] * n_lists

#     for i in range(n_lists):
#         for i2, c in enumerate(command[i]):
#             if i2 == 0 and c == 0 and (len(command[i]) == 1 or command[i][i2+1] == 0):
#                 duration[i] += 1
            
#             if i2%2 == 0:
#                 duration[i] += c * time_per_turn
#             else:
#                 if i2%2 == 1:
#                     duration[i] += c * time_per_line
    
#     return duration

def int_to_string_command(command):
    ''' converts the command from a list of integers to a string that can be 
    sent to the robots. 
     Note that command may be a list of lists, so need to get to the bottom lists 
    before converting to a string. '''

    # determine if command contains lists or numbers
    if type(command[0]) == list:
        n_lists = len(command)
    else:
        n_lists = 1
        command = [command]

    string_command = [''] * n_lists

    for i in range(n_lists):
        string_command[i] = '99, '
        for c in command[i]:
            string_command[i] += str(c) + ', '
        string_command[i] = string_command[i][:-2]

    if n_lists == 1:
        string_command = string_command[0]

    return string_command


def paths_to_commands(robots, paths, map):
    ''' converts the paths in paths to commands that can be sent to the robots.
     The commands take the form of a series of turns and linear movements: 
      e.g. the command [2,1,4,2] would tell the robot to turn clockwise by
      2 lines, then move forward 1 line, then turn counter-clockwise by 4 
      (i.e. 6-2) lines, then forward 2 lines'''
    
    # get the moving robots
    moving_robots = robots.get_moving_robots()
    robot_list = list(moving_robots.members.keys())

    commands = {}
    command_strings = {}
    orientations = {}

    # loop through each robot and convert its path to a series of commands
    for key, path in paths.items():
        command_string, command, orientation = path_to_command(moving_robots.members[key], path, map) 
        commands[key] = command       
        command_strings[key] = command_string
        orientations[key] = orientation    

    # check if the robots both have any zero commands before 
    # they start moving (i.e. if they are already in the correct positions)   
    while True:
        if commands[robot_list[0]][0] == [0] and commands[robot_list[1]][0] == [0]:
            for key in commands.keys():
                # remove the first command from each list
                command_strings[key] = command_strings[key][1:]
                commands[key] = commands[key][1:]
        else:
            break
            
    return command_strings, commands, orientations


def split_off_initial_turn(paths):
    robot_list = list(paths.commands.keys())    
    if len(paths.commands[robot_list[0]][0]) == 1 and len(paths.commands[robot_list[1]][0]) == 1:
        # both robots have a single command in their first list
        # so split off the first command from each robot
        initial_turns = copy.deepcopy(paths)
             
        for key in robot_list:
            initial_turns.command_strings[key] = [initial_turns.command_strings[key][0]]
            initial_turns.orientations[key] = [initial_turns.orientations[key][0]]
            initial_turns.commands[key] = [initial_turns.commands[key][0]]

            paths.command_strings[key] = paths.command_strings[key][1:]
            paths.orientations[key] = paths.orientations[key][1:]
            paths.commands[key] = paths.commands[key][1:]

        return initial_turns
    
    else:
        return None




# def paths_to_commands(robots, paths, map, time_per_turn = 0.5, time_per_line = 1.):
#     ''' converts the paths in paths to commands that can be sent to the robots.
#      The commands take the form of a series of turns and linear movements: 
#       e.g. the command [2,1,4,2] would tell the robot to turn clockwise by
#       2 lines, then move forward 1 line, then turn counter-clockwise by 4 
#       (i.e. 6-2) lines, then forward 2 lines'''
    
#     # get the moving robots
#     moving_robots = robots.get_moving_robots()
#     robot_list = list(moving_robots.members.keys())

#     commands = {}
#     durations = {}
#     command_strings = {}
#     final_orientations = {}

#     # loop through each robot and convert its path to a series of commands
#     for key, path in paths.items():
#         command_string, duration, command, orientation = path_to_command(moving_robots.members[key], path, map, time_per_turn, time_per_line) 
#         commands[key] = command       
#         durations[key] = duration
#         command_strings[key] = command_string
#         final_orientations[key] = orientation
    

#     # check if the robots both have any zero commands before 
#     # they start moving (i.e. if they are already in the correct positions)
    
    
#     while True:
#         if commands[robot_list[0]][0] == [0] and commands[robot_list[1]][0] == [0]:
#             for key in commands.keys():
#                 # remove the first command from each list
#                 command_strings[key] = command_strings[key][1:]
#                 durations[key] = durations[key][1:]
#                 commands[key] = commands[key][1:]
#         else:
#             break
            
#     return command_strings, durations, commands, final_orientations



def plot_paths(map, robots, optimal_paths):
    ''' plots the paths in optimal_paths on the map. '''
       
    # create empty list of platforms for setting axis limits
    # create list of 2 empty lists 
    platforms = [[], []]

    # create figure with 2 subplots arranged horizontally
    # Figure should open on screen 1 at top level    
    fig, ax = plt.subplots(1, 2, figsize=(20,10))

    # get stationary robot position 
    stat_robot = robots.get_stat_robot()
    stat_robot_pos = stat_robot.position
    # plot hexagon at stat_robot_pos
    for a in range(2):
        platforms[a].append(stat_robot_pos)
        draw_platform(map, stat_robot_pos, ax[a], color='b')

    # get moving robot positions
    moving_robots = robots.get_moving_robots()
    mov_colors = [['r', 'g'], ['tab:red', 'tab:green']]
    # plot hexagons at moving robot positions
    for a in range(2):
        c_ind = 0
        for key, r in moving_robots.members.items():
            platforms[a].append(r.position)        
            draw_platform(map, r.position, ax[a], color=mov_colors[a][c_ind])
            c_ind += 1

    # plot optimal paths in second subplot
    c_ind = 0
    for key, path in optimal_paths.items():
        color=mov_colors[0][c_ind]
        c_ind += 1
        for p in path:
            platforms[1].append(p)
            draw_platform(map, p, ax[1], color=color)

    # set axis limits and reverse y axis
    # x_min = None
    # x_max = None
    # y_min = None
    # y_max = None

    # platforms_all = platforms[0] + platforms[1]
    # for p in platforms_all:
    #     plat_pos = map.cartesian_position(p)
    #     if x_min == None or plat_pos[0] < x_min:
    #         x_min = plat_pos[0]
    #     if x_max == None or plat_pos[0] > x_max:
    #         x_max = plat_pos[0]
    #     if y_min == None or plat_pos[1] < y_min:
    #         y_min = plat_pos[1]
    #     if y_max == None or plat_pos[1] > y_max:
    #         y_max = plat_pos[1]

    
    stat_cart_pos = map.cartesian_position(stat_robot_pos)
    axis_half_width = 5
    x_min = stat_cart_pos[0] - axis_half_width
    x_max = stat_cart_pos[0] + axis_half_width
    y_min = stat_cart_pos[1] - axis_half_width
    y_max = stat_cart_pos[1] + axis_half_width

    # plot all other platforms within the axis limits as white hexagons
    for a in range(2):
        for p in map.platform_list():
            if p not in platforms[a]:
                pos = map.cartesian_position(p)
                if pos[0] >= x_min-1 and pos[0] <= x_max+1 and \
                    pos[1] >= y_min-1 and pos[1] <= y_max+1:
                    draw_platform(map, p, ax[a], color='w') 

    # set axis limits
    for a in ax:
        a.set_xlim(x_min-1, x_max+1)
        a.set_ylim(y_min-1, y_max+1)

        #  flip y axis
        a.invert_yaxis()

        # make x and y axis scales equal
        a.set_aspect('equal')

        for t in a.texts:
            t.set_clip_on(True)

    # os.environ['DISPLAY'] = ':0.1'
    fig.canvas.manager.window.wm_geometry("800x600+0+0")
    fig.canvas.manager.window.wm_attributes('-topmost', 1)
    plt.show(block=False)


    # return the figure handle
    return fig

def close_paths_plot(fig):
    import matplotlib.pyplot as plt
    plt.close(fig)

def draw_platform(map, pos, ax, color='r'):
    ''' draws a platform on the map '''
    import matplotlib.patches as patches

    plat_pos = map.cartesian_position(pos)

    # draw a hexagon at plat_pos with edges of length 1
    hexagon = patches.RegularPolygon((plat_pos[0], plat_pos[1]),
                                    numVertices=6, radius=1,
                                    orientation=np.pi/2,
                                    facecolor=color, edgecolor='k')
    ax.add_patch(hexagon)

    # overlay the platform number
    text_col = 'k' if color == 'w' else 'w'
    ax.text(plat_pos[0], plat_pos[1], int(pos), ha='center', va='center', color=text_col)

    return hexagon

   

if __name__ == '__main__':
    # directory = '/media/jake/LaCie/robot_maze_workspace'
    directory = 'D:/testFolder/pico_robots/map'
    # directory = 'C:/Users/Jake/Desktop/map_of_platforms'
    # map = platform_map.open_map(map='restricted_map', directory=directory)
    map = Map(directory=directory)
    map.goal_position = 156

    robot1 = Robot(1, '192.100.0.101', 1025, 61, 180, 'stationary', map)
    robot2 = Robot(2, '192.100.0.102', 1026, 89, 0, 'moving', map)
    robot3 = Robot(3, '192.100.0.103', 1027, 90, 0, 'moving', map)

    # robot2 = Robot(2, '192.100.0.102', 1026, 89, 0, 'moving', map)
    # robot3 = Robot(3, '192.100.0.103', 1027, 90, 0, 'moving', map)

    robots = Robots()
    robots.add_robots([robot1, robot2, robot3])

    next_plats = [42, 70]    
    # initial_positions = get_starting_positions(robots, map)
    # paths = get_all_paths(robots, next_plats, map)
    # optimal_paths = select_optimal_paths(paths, robots, next_plats, map)
    # print(optimal_paths)

    # paths = Paths(robots, map, next_positions=[52, 42])
    paths = Paths(robots, map, next_positions=[42, 70])

    paths.plot_paths(robots, map)
    
    initial_turns = paths.split_off_initial_turn()
    # commands, durations, _, final_orientations = paths_to_commands(robots, optimal_paths, map)
    
    # plt.show()
    # initial_turns, paths = split_off_initial_turn(paths)

    paths.close_paths_plot()