'''
Defines a class that creates a path for the robot to follow, given a start
and end position.
It requires methods to create paths given certain constraints, such as
the shortest path, a path that avoids other robots or obstacles, etc.
'''
import sys
# sys.path.append('/home/jake/Documents/robot_maze/workstation')
sys.path.append('C:/Users/LabUser/Documents/robot_maze/workstation')


import numpy as np
import copy
from honeycomb_task.platform_map import Map
import time

# CreatePath should take a start and end position, and optionally a 
# list of positions to avoid
class Paths:
    def __init__(self, robots, map, next_positions=None, task='task', \
                 difficulty = 'hard', start = False, choices = None):
        
        if task == 'task':       
            if next_positions is None:
                # pick next positions
                self.next_plats = get_next_positions(robots, map, choices, difficulty)

            else:
                self.next_plats = next_positions
                
            # get starting shape (i.e. straightline, boomerang, or triangle)
            self.start_shape = map.get_shape(robots)

            positions = [robots.get_stat_robot().position, self.next_plats[0], self.next_plats[1]]

            self.end_shape = map.get_shape_from_positions(positions)

            self.select_targets(robots, map)
            
            
            # get all possible paths
            start_time = time.time()
            # self.all_paths = get_all_paths(robots, self.next_plats, map)
            self.all_paths = get_all_paths_new(self, robots, map)
            stop_time = time.time()
            print(f'get_all_paths took {stop_time - start_time} seconds')

            # for key, value in self.targets.items():
            #     self.all_paths[key] = self.all_paths[key][f'to_plat{value}']

            # select the optimal paths
            start_time = time.time()
            self.optimal_paths = select_optimal_paths_new(self, robots, map)
            stop_time = time.time()
            print(f'select_optimal_paths took {stop_time - start_time} seconds')
            pass

            
        elif task == 'task_2goal':
            # if stationary robot is at the mirror_goal position, then use get_all_paths
            stat_robot = robots.get_stat_robot()
            stat_robot_pos = stat_robot.position

            # get the mirror goal position
            mirror_goal = map.mirror_position

            if stat_robot_pos == mirror_goal:
                self.next_plats = get_next_positions(robots, map, choices, 'hard')

            elif next_positions is None:
                # pick next positions
                self.next_plats = get_next_positions_2goal(robots, map, choices)

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
            
            # determining if the 2 robots have overlapping sets of next platforms
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
        if hasattr(self, 'fig_handle'):
            close_paths_plot(self.fig_handle)
            self.fig_handle = None
        return
    

    def select_targets(self, robots, map):

        stat_robot = robots.get_stat_robot()
        moving_robots = robots.get_moving_robots()
        moving_robot_ids = list(moving_robots.members.keys())
        moving_robot_positions = moving_robots.get_positions()
        directions = 'clockwise', 'anticlockwise'
        targets = {moving_robot_ids[0]: None, moving_robot_ids[1]: None}

        if self.start_shape == 'trial_start':
            moving_robot1 = moving_robot_ids[0] 
            moving_robot2 = moving_robot_ids[1]

            dist1_1 = map.find_shortest_distance(robots.members[moving_robot1].position, self.next_plats[0])
            dist1_2 = map.find_shortest_distance(robots.members[moving_robot1].position, self.next_plats[1])

            dist2_1 = map.find_shortest_distance(robots.members[moving_robot2].position, self.next_plats[0])
            dist2_2 = map.find_shortest_distance(robots.members[moving_robot2].position, self.next_plats[1])

            if self.end_shape == 'line':
                if dist1_1 == dist2_1:
                    targets[moving_robot1] = self.next_plats[0]
                    targets[moving_robot2] = self.next_plats[1]
                
                elif dist1_1 == 1 or dist2_2 == 1:
                    targets[moving_robot1] = self.next_plats[0]
                    targets[moving_robot2] = self.next_plats[1]

                else:
                    targets[moving_robot1] = self.next_plats[1]
                    targets[moving_robot2] = self.next_plats[0]
                
            elif self.end_shape == 'boomerang':
                if dist1_1 == dist2_2 and dist1_2 == dist2_1:
                    if dist1_1 < dist1_2:
                        targets[moving_robot1] = self.next_plats[0]
                        targets[moving_robot2] = self.next_plats[1]
                    
                    else:
                        targets[moving_robot1] = self.next_plats[1]
                        targets[moving_robot2] = self.next_plats[0]
                    
                else:
                    if max(dist1_1, dist2_2) == 3 and max(dist1_2, dist2_1) == 3:
                        if dist1_1 == 1 or dist2_2 == 1:
                            targets[moving_robot1] = self.next_plats[0]
                            targets[moving_robot2] = self.next_plats[1]
                        else:
                            targets[moving_robot1] = self.next_plats[1]
                            targets[moving_robot2] = self.next_plats[0]

                    elif dist1_1 == 3 or dist2_2 == 3:
                        targets[moving_robot1] = self.next_plats[1]
                        targets[moving_robot2] = self.next_plats[0]
                    else:
                        targets[moving_robot1] = self.next_plats[0]
                        targets[moving_robot2] = self.next_plats[1]

            else: # end_shape is triangle
                if dist1_1 == 1 and dist1_2 == 1:
                    if dist2_1 == 2:
                        targets[moving_robot1] = self.next_plats[0]
                        targets[moving_robot2] = self.next_plats[1]
                    else:
                        targets[moving_robot1] = self.next_plats[1]
                        targets[moving_robot2] = self.next_plats[0]

                elif dist2_1 == 1 and dist2_2 == 1:
                    if dist1_1 == 2:
                        targets[moving_robot1] = self.next_plats[1]
                        targets[moving_robot2] = self.next_plats[0]
                    else:
                        targets[moving_robot1] = self.next_plats[0]
                        targets[moving_robot2] = self.next_plats[1]

                elif dist1_1 == 1 or dist2_2 == 1:
                    targets[moving_robot1] = self.next_plats[0]
                    targets[moving_robot2] = self.next_plats[1]
                
                elif dist1_2 == 1 or dist2_1 == 1:
                    targets[moving_robot1] = self.next_plats[1]
                    targets[moving_robot2] = self.next_plats[0]

                elif dist1_1 == 2 or dist2_2 == 2:
                    targets[moving_robot1] = self.next_plats[0]
                    targets[moving_robot2] = self.next_plats[1]
                
                elif dist1_2 == 2 or dist2_1 == 2:
                    targets[moving_robot1] = self.next_plats[1]
                    targets[moving_robot2] = self.next_plats[0]

                elif dist1_1 == 3 and dist1_2 == 3:
                    if dist2_1 == 2:
                        targets[moving_robot1] = self.next_plats[1]
                        targets[moving_robot2] = self.next_plats[0]
                    else:
                        targets[moving_robot1] = self.next_plats[0]
                        targets[moving_robot2] = self.next_plats[1]

                elif dist2_1 == 3 and dist2_2 == 3:
                    if dist1_1 == 2:
                        targets[moving_robot1] = self.next_plats[0]
                        targets[moving_robot2] = self.next_plats[1]
                    else:
                        targets[moving_robot1] = self.next_plats[1]
                        targets[moving_robot2] = self.next_plats[0]

            self.targets = targets
            return  
        
        if self.start_shape == 'line' or self.start_shape == 'boomerang':
            # find the moving robot at the end of the line
            for r in range(2):
                if map.check_adjacent(moving_robot_positions[r], stat_robot.position):
                    middle_robot = moving_robot_ids[r]
                    break
            end_robot = moving_robot_ids[0] if middle_robot == moving_robot_ids[1] else moving_robot_ids[1]

            end_dist1 = map.find_shortest_distance(robots.members[end_robot].position, self.next_plats[0])
            end_dist2 = map.find_shortest_distance(robots.members[end_robot].position, self.next_plats[1])

            middle_dist1 = map.find_shortest_distance(robots.members[middle_robot].position, self.next_plats[0])
            middle_dist2 = map.find_shortest_distance(robots.members[middle_robot].position, self.next_plats[1])


        ############################ LINE ############################# 
        if self.start_shape == 'line':          

            if end_dist1 < end_dist2:
                end_robot_target = self.next_plats[0]
                middle_robot_target = self.next_plats[1]
            else:
                end_robot_target = self.next_plats[1]
                middle_robot_target = self.next_plats[0]

            self.targets = {end_robot: end_robot_target, middle_robot: middle_robot_target}
            return

        ############################ BOOMERANG #############################
        if self.start_shape == 'boomerang':

            if self.end_shape == 'line':
                if end_dist1 == end_dist2:
                    if middle_dist1 < middle_dist2:
                        end_robot_target = self.next_plats[1]
                        middle_robot_target = self.next_plats[0]
                    else:
                        end_robot_target = self.next_plats[0]
                        middle_robot_target = self.next_plats[1]

                elif middle_dist1 == 0 or middle_dist2 == 0:
                    if middle_dist1 == 0:
                        end_robot_target = self.next_plats[1]
                        middle_robot_target = self.next_plats[0]
                    else:
                        end_robot_target = self.next_plats[0]
                        middle_robot_target = self.next_plats[1]

                else:
                    if end_dist1 < end_dist2:
                        end_robot_target = self.next_plats[0]
                        middle_robot_target = self.next_plats[1]
                    else:
                        end_robot_target = self.next_plats[1]
                        middle_robot_target = self.next_plats[0]
            

            elif self.end_shape == 'boomerang':

                if middle_dist1 == 0 or middle_dist2 == 0:                
                    if middle_dist1 == 0:                
                        if middle_dist2 == end_dist2:
                            end_robot_target = self.next_plats[1]
                            middle_robot_target = self.next_plats[0]

                        else:
                            end_robot_target = self.next_plats[0]
                            middle_robot_target = self.next_plats[1]
                        
                    else:
                        if middle_dist1 == end_dist1:
                            end_robot_target = self.next_plats[0]
                            middle_robot_target = self.next_plats[1]
                        else:
                            end_robot_target = self.next_plats[1]
                            middle_robot_target = self.next_plats[0]

                # else if both the middle and end robots lie on an axis with one of the new positions, 
                # then middle robot moves to this position
                elif map.get_common_axis_from_positions([robots.members[middle_robot].position, \
                        robots.members[end_robot].position, self.next_plats[0]])[0] is not None:
                    end_robot_target = self.next_plats[1]
                    middle_robot_target = self.next_plats[0]                                                
                         
                elif map.get_common_axis_from_positions([robots.members[middle_robot].position, \
                        robots.members[end_robot].position, self.next_plats[1]])[0] is not None:
                    end_robot_target = self.next_plats[0]
                    middle_robot_target = self.next_plats[1]

                else:
                    if end_dist1 < end_dist2:
                        end_robot_target = self.next_plats[0]
                        middle_robot_target = self.next_plats[1]
                    else:
                        end_robot_target = self.next_plats[1]
                        middle_robot_target = self.next_plats[0]   

            else: # end shape is triangle
                if middle_dist1 == 0 or middle_dist2 == 0:
                    if middle_dist1 == 0:
                        if end_dist2 == 1:
                            end_robot_target = self.next_plats[1]
                            middle_robot_target = self.next_plats[0]

                        else: # end_dist2 == 2
                            end_robot_target = self.next_plats[0]
                            middle_robot_target = self.next_plats[1]
                    
                    else: # middle_dist2 == 0
                        if end_dist1 == 1:
                            end_robot_target = self.next_plats[0]
                            middle_robot_target = self.next_plats[1]
                        
                        else: # end_dist1 == 2
                            end_robot_target = self.next_plats[1]
                            middle_robot_target = self.next_plats[0]

                elif middle_dist1 == 1 and end_dist1 == 2:
                    end_robot_target = self.next_plats[1]
                    middle_robot_target = self.next_plats[0]

                elif middle_dist2 == 1 and end_dist2 == 2:
                    end_robot_target = self.next_plats[0]
                    middle_robot_target = self.next_plats[1]

                elif middle_dist1 == 1 and end_dist1 == 1:
                    end_robot_target = self.next_plats[0]
                    middle_robot_target = self.next_plats[1]

                elif middle_dist2 == 1 and end_dist2 == 1:
                    end_robot_target = self.next_plats[1]
                    middle_robot_target = self.next_plats[0]

                elif end_dist1== 3 and end_dist2 == 3:
                    if middle_dist1 == 2:
                        end_robot_target = self.next_plats[1]
                        middle_robot_target = self.next_plats[0]
                    else:
                        end_robot_target = self.next_plats[0]
                        middle_robot_target = self.next_plats[1]

                elif end_dist1 == 2:
                    end_robot_target = self.next_plats[0]
                    middle_robot_target = self.next_plats[1]
                
                else:
                    end_robot_target = self.next_plats[1]
                    middle_robot_target = self.next_plats[0]
                    
            self.targets = {end_robot: end_robot_target, middle_robot: middle_robot_target}
            return

        ############################ TRIANGLE #############################
        if self.start_shape == 'triangle':

            moving_robot1 = moving_robot_ids[0] 
            moving_robot2 = moving_robot_ids[1]

            dist1_1 = map.find_shortest_distance(robots.members[moving_robot1].position, self.next_plats[0])
            dist1_2 = map.find_shortest_distance(robots.members[moving_robot1].position, self.next_plats[1])

            dist2_1 = map.find_shortest_distance(robots.members[moving_robot2].position, self.next_plats[0])
            dist2_2 = map.find_shortest_distance(robots.members[moving_robot2].position, self.next_plats[1])

            if self.end_shape == 'line':
                # if neither robot is at a new location, they each go to their closest new location
                if dist1_1 == 0 or dist2_2 == 0 or dist1_1 < dist1_2:
                    self.targets = {moving_robot1: self.next_plats[0], moving_robot2: self.next_plats[1]}
                elif dist1_2 == 0 or dist2_1 == 0 or dist1_2 < dist1_1:
                    self.targets = {moving_robot1: self.next_plats[1], moving_robot2: self.next_plats[0]}

            elif self.end_shape == 'boomerang':
                if dist1_1 == 0 or dist2_2 == 0:
                    self.targets = {moving_robot1: self.next_plats[0], moving_robot2: self.next_plats[1]}
                elif dist1_2 == 0 or dist2_1 == 0:
                    self.targets = {moving_robot1: self.next_plats[1], moving_robot2: self.next_plats[0]}

                elif dist1_1 == 1 or dist2_2 == 1:
                    self.targets = {moving_robot1: self.next_plats[0], moving_robot2: self.next_plats[1]}
                else:
                    self.targets = {moving_robot1: self.next_plats[1], moving_robot2: self.next_plats[0]}
                
        
            elif self.end_shape == 'triangle':
                if dist1_1 == 0 or dist2_2 == 0:
                    self.targets = {moving_robot1: self.next_plats[0], moving_robot2: self.next_plats[1]}
                elif dist1_2 == 0 or dist2_1 == 0:
                    self.targets = {moving_robot1: self.next_plats[1], moving_robot2: self.next_plats[0]}
                elif dist1_1 == 1 or  dist2_2 == 1:
                        self.targets = {moving_robot1: self.next_plats[0], moving_robot2: self.next_plats[1]}
                elif dist1_2 == 1 or dist2_1 == 1:
                        self.targets = {moving_robot1: self.next_plats[1], moving_robot2: self.next_plats[0]}
                elif dist1_1 < dist1_2:
                    self.targets = {moving_robot1: self.next_plats[0], moving_robot2: self.next_plats[1]}
                # else robot goes to position it does NOT share a common axis with
                else:
                    if map.get_common_axis_from_positions([robots.members[moving_robot1].position, self.next_plats[0]])[0] is not None:
                        self.targets = {moving_robot1: self.next_plats[1], moving_robot2: self.next_plats[0]}
                    else:
                        self.targets = {moving_robot1: self.next_plats[0], moving_robot2: self.next_plats[1]}                        
            
            return
        

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
    
    # get all possible pairs
    # get first order ring around stationary robot
    stat_robot = robots.get_stat_robot()
    stat_robot_pos = stat_robot.position
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


    # remove pairs that don't satisfy distance criteria
    # get stationary robot's distance to goal    
    stat_dist = map.cartesian_distance(stat_robot_pos, map.goal_position)
    # loop through each pair, removing pairs where neither member has shorter
    # distance to goal than stat_robot_pos
    row = 0
    n_possible_pairs = possible_pairs.shape[0]
    while row < n_possible_pairs:
        p = possible_pairs[row,:]
        p0_dist = map.cartesian_distance(p[0], map.goal_position)
        p1_dist = map.cartesian_distance(p[1], map.goal_position)

        if difficulty == 'hard':
            if p0_dist >= stat_dist and p1_dist >= stat_dist:
                # delete row from possible_pairs
                possible_pairs = np.delete(possible_pairs, row, axis=0)
                n_possible_pairs -= 1
            else:
                row += 1

        if difficulty == 'easy':
            if (p0_dist > stat_dist or p1_dist > stat_dist) or \
                    (p0_dist == stat_dist and p1_dist == stat_dist) or \
                         ((p0_dist == stat_dist or p1_dist == stat_dist) \
                          and not map.check_adjacent(stat_robot_pos, map.goal_position)):
                                # delete row from possible_pairs
                possible_pairs = np.delete(possible_pairs, row, axis=0)
                n_possible_pairs -= 1
            else:
                row += 1

    
    # find what, if any, choices have previously been made from stat_robot_pos using 
    # the choices.data pandas dataframe
    if choices != None:
        choicesFromStart = choices.data[choices.data['start_pos'] == stat_robot_pos]
        # extract the chosen and unchosen positions to a numpy array and remove 
        # any repeated pairs
        n_prev_pairs = 0
        if choicesFromStart.empty == False:
            previous_pairs = choicesFromStart[['chosen_pos', 'unchosen_pos']].to_numpy()
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
    
    # randomly reorder possible_pairs and select next positions
    np.random.shuffle(possible_pairs)
    next_positions = possible_pairs[0]    

    return next_positions

def get_next_positions_2goal(robots, map, choices):

    # get all possible pairs
    # get first order ring around stationary robot
    stat_robot = robots.get_stat_robot()
    stat_robot_pos = stat_robot.position
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


    # remove pairs that don't satisfy distance criteria
    # get stationary robot's distance to goal    
    stat_dist = map.cartesian_distance(stat_robot_pos, map.goal_position)
    statm_dist = map.cartesian_distance(stat_robot_pos, map.mirror_position)
    # loop through each pair, removing pairs where neither member has shorter
    # distance to goal than stat_robot_pos
    row = 0
    n_possible_pairs = possible_pairs.shape[0]
    while row < n_possible_pairs:
        p = possible_pairs[row,:]
        p0_dist = map.cartesian_distance(p[0], map.goal_position)
        p1_dist = map.cartesian_distance(p[1], map.goal_position)

        p0m_dist = map.cartesian_distance(p[0], map.mirror_position)
        p1m_dist = map.cartesian_distance(p[1], map.mirror_position)

        if (p0_dist >= stat_dist or p1m_dist >= statm_dist) and \
            (p1_dist >= stat_dist or p0m_dist >= statm_dist):
            # delete row from possible_pairs
            possible_pairs = np.delete(possible_pairs, row, axis=0)
            n_possible_pairs -= 1
        else:
            row += 1

    # find what, if any, choices have previously been made from stat_robot_pos using 
    # the choices.data pandas dataframe
    # if choices != None:
    #     choicesFromStart = choices.data[choices.data['start_pos'] == stat_robot_pos]
    #     # extract the chosen and unchosen positions to a numpy array and remove 
    #     # any repeated pairs
    #     n_prev_pairs = 0
    #     if choicesFromStart.empty == False:
    #         previous_pairs = choicesFromStart[['chosen_pos', 'unchosen_pos']].to_numpy()
    #         previous_pairs = previous_pairs.astype(int)
    #         for p in range(previous_pairs.shape[0]):
    #             previous_pairs[p] = np.sort(previous_pairs[p])
    #         # remove duplicate pairs
    #         previous_pairs = np.unique(previous_pairs, axis=0)
    #         n_prev_pairs = previous_pairs.shape[0]

    #         if n_prev_pairs != n_possible_pairs: # remove common pairs
    #             for p in previous_pairs:
    #                 if p in possible_pairs:
    #                     # find row index of p in possible pairs
    #                     row_ind = np.where(np.all(possible_pairs == p, axis=1))[0][0]
    #                     # delete row from possible_pairs
    #                     possible_pairs = np.delete(possible_pairs, row_ind, axis=0)
    
    # randomly reorder possible_pairs and select next positions
    np.random.shuffle(possible_pairs)
    next_positions = possible_pairs[0]    

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


def get_all_paths_new(paths, robots, map):
    ''' determines the paths the moving robot can take to reach
    the required position adjacent to the stationary robot'''

    # first, verify that next platforms are adjacent to the stationary robot
    stat_robot = robots.get_stat_robot()
    # get stationary robot's first order ring
    stat_robot_ring = map.get_ring_around_position(stat_robot.position, 1)
    # verify that next_plats are in stat_robot_ring
    next_plats = paths.next_plats
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
    paths_all = {}
    for key, r in moving_robots.members.items():      
        paths_all[key] = {}

        p2 = paths.targets[key]


        for p in initial_positions[key]:  
            paths_all[key][f'from_plat{p}'] = {}        
            for d in directions:
                paths_all[key][f'from_plat{p}'][d] = {}

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
                
                paths_all[key][f'from_plat{p}'][d] = path

    return paths_all



def select_optimal_paths_new(paths, robots, map):
    ''' selects the optimal paths from the set of all paths. The rules are 
    1) the paths can't intersect (if robots moving in opposite directions), 
    2) can't start or finish on the same platform or occupy the same position
    at the same time step, 
    
    Oct 5, 2023: inserting 3) robots that are initially adjacent can't move to
    another position where they are still adjacent (as the chances of them 
    hitting each other are too high) 
    Oct 4, 2023: need to be more stringent, can't have robots becoming adjacent either, 
    except at the end

    4) robots shouldn't follow each other, even with a gap of 1 (that being said, 
    such paths probably won't meet all the other criteria anyways, and I think were
    only occurring because of bugs - Jake 2023-10-12)

    5) and should have the shortest possible length, 
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
    

    p = paths.targets[moving_robot_ids[0]]

    p2 = paths.targets[moving_robot_ids[1]]

    # get all paths from paths[moving_robot_ids[0]][f'to_plat{p}'] 
    start1 = robots.members[moving_robot_ids[0]].position
    paths1 = paths.all_paths[moving_robot_ids[0]]

    start2 = robots.members[moving_robot_ids[1]].position
    paths2 = paths.all_paths[moving_robot_ids[1]]
    

    for path1_both_dir in paths1.values():
        for d in directions:
            path1 = path1_both_dir[d]

            for path2_both_dir in paths2.values():
                
                if d == 'clockwise':
                    d2 = 'anticlockwise'
                else:
                    d2 = 'clockwise'

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

                # 3) robots that are initially adjacent can't move to adjacent positions
                # if start1 and start2 are adjacent, check if first path positions are adjacent
                
                if map.check_robots_adjacent(robots) and \
                    map.check_adjacent(path1[0], path2[0]):
                    continue

                adj_counter = 0
                break_flag = False
                for s in range(max_path_length):
                    if s >= min_path_length:
                        if len(path1) == min_path_length:
                            path1_plat = path1[-1]
                            path2_plat = path2[s]
                        else:
                            path1_plat = path1[s]
                            path2_plat = path2[-1]
                    else:
                        path1_plat = path1[s]
                        path2_plat = path2[s]
                                                
                    
                    if path1_plat == path2_plat:
                        break_flag = True
                        break
                    elif map.check_adjacent(path1_plat, path2_plat):
                        adj_counter += 1                            

                if break_flag or adj_counter > 1:
                    continue

                # 4) if one robot is following the other, even with a gap of 1 platform,
                # there is the potential for the following robot to hit the leading robot 
                path1_length = len(path1)
                path2_length = len(path2)
                if path1_length > 2 and path2_length > 2:
                    distance = []
                    for pos in range(2):
                        distance.append(map.find_shortest_distance(path1[pos], path2[pos]))
                    if distance[0] <= 2 and distance[1] <= 2:
                        continue 

                # 5) should have the shortest possible length                      
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



def select_optimal_paths(paths, robots, next_plats, map):
    ''' selects the optimal paths from the set of all paths. The rules are 
    1) the paths can't intersect (if robots moving in opposite directions), 
    2) can't start or finish on the same platform or occupy the same position
    at the same time step, 
    
    Oct 5, 2023: inserting 3) robots that are initially adjacent can't move to
    another position where they are still adjacent (as the chances of them 
    hitting each other are too high) 
    Oct 4, 2023: need to be more stringent, can't have robots becoming adjacent either, 
    except at the end

    4) robots shouldn't follow each other, even with a gap of 1 (that being said, 
    such paths probably won't meet all the other criteria anyways, and I think were
    only occurring because of bugs - Jake 2023-10-12)

    5) and should have the shortest possible length, 
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
        start1 = robots.members[moving_robot_ids[0]].position
        paths1 = paths[moving_robot_ids[0]][f'to_plat{p}']

        start2 = robots.members[moving_robot_ids[1]].position
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

                        # 3) robots that are initially adjacent can't move to adjacent positions
                        # if start1 and start2 are adjacent, check if first path positions are adjacent
                        
                        if map.check_robots_adjacent(robots) and \
                            map.check_adjacent(path1[0], path2[0]):
                            continue

                        adj_counter = 0
                        break_flag = False
                        for s in range(max_path_length):
                            if s >= min_path_length:
                                if len(path1) == min_path_length:
                                    path1_plat = path1[-1]
                                    path2_plat = path2[s]
                                else:
                                    path1_plat = path1[s]
                                    path2_plat = path2[-1]
                            else:
                                path1_plat = path1[s]
                                path2_plat = path2[s]
                                                        
                            
                            if path1_plat == path2_plat:
                                break_flag = True
                                break
                            elif map.check_adjacent(path1_plat, path2_plat):
                                adj_counter += 1                            

                        if break_flag or adj_counter > 1:
                            continue

                        # 4) if one robot is following the other, even with a gap of 1 platform,
                        # there is the potential for the following robot to hit the leading robot 
                        path1_length = len(path1)
                        path2_length = len(path2)
                        if path1_length > 2 and path2_length > 2:
                            distance = []
                            for pos in range(2):
                                distance.append(map.find_shortest_distance(path1[pos], path2[pos]))
                            if distance[0] <= 2 and distance[1] <= 2:
                                continue 

                        # 5) should have the shortest possible length                      
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
    
    if len(path) == 1:
        if path[0] == robot.position:
            subcommands = [[0], [0], [0]]
            command_string = int_to_string_command(subcommands)
            # suborientations is a list of lists, where each list contains the
            # orientation of the robot
            suborientations = [[robot.orientation] for _ in range(3)]
            return command_string, subcommands, suborientations
              
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

    
    if subcommands[-1][-1] > 1:
        if len(subcommands[-2])%2 == 0:
            subcommands[-2][-1] = subcommands[-2][-1] + \
                (subcommands[-1][-1] - 1)

        else:
            subcommands[-2].append(subcommands[-1][-1] - 1)

        subcommands[-1][-1] -= 1
    # duration = get_command_timing(subcommands, time_per_turn = 0.5, time_per_line = 1.)

    command_string = int_to_string_command(subcommands)

    return command_string, subcommands, suborientations


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
    if len(robot_list) > 1:
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


if __name__ == '__main__':
    # __package__ = "honeycomb_task"
    # directory = '/media/jake/LaCie/robot_maze_workspace'
    # directory = 'D:/testFolder/pico_robots/map'
    # directory = 'C:/Users/Jake/Documents/robot_maze'
    # directory = 'C:/Users/Jake/Desktop/map_of_platforms'
    # directory = '/home/jake/Documents/robot_maze/workstation/map_files'
    directory = 'C:/Users/LabUser/Documents/robot_maze/workstation/map_files'
    
    # map = platform_map.open_map(map='restricted_map', directory=directory)
    
    map = Map(directory=directory)
    map.goal_position = 146

    from robot import Robot, Robots 

    robot1 = Robot(1, '192.168.0.102', 65535, 119, 0, 'stationary')
    robot2 = Robot(2, '192.168.0.103', 65534, 91, 180, 'moving')
    robot3 = Robot(3, '192.168.0.104', 65533, 100, 300, 'moving')

   
    robots = Robots()
    robots.add_robots([robot1, robot2, robot3])
    # yaml_dir = 'D:/testFolder/pico_robots/yaml'
    # robots = Robots.from_yaml(yaml_dir)


    next_plats = [100, 109]    
    # initial_positions = get_starting_positions(robots, map)
    # paths = get_all_paths(robots, next_plats, map)
    # optimal_paths = select_optimal_paths(paths, robots, next_plats, map)
    # print(optimal_paths)


    # next_plats = get_next_positions(robots, map, None, 'hard')
    # print(next_plats)

    # paths = Paths(robots, map, next_positions=[52, 42])
    paths = Paths(robots, map, next_positions=next_plats)

    paths.plot_paths(robots, map)
    
    initial_turns = paths.split_off_initial_turn()
    # commands, durations, _, final_orientations = paths_to_commands(robots, optimal_paths, map)
    
    # plt.show()
    # initial_turns, paths = split_off_initial_turn(paths)

    from send_over_socket import send_over_sockets_threads
    send_over_sockets_threads(robots, initial_turns)

    send_over_sockets_threads(robots, paths)
    paths.close_paths_plot()

    robots.update_positions(paths) 