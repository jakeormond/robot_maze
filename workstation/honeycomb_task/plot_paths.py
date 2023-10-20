'''
Defines a class that creates a path for the robot to follow, given a start
and end position.
It requires methods to create paths given certain constraints, such as
the shortest path, a path that avoids other robots or obstacles, etc.
'''
import numpy as np
import copy
from .platform_map import Map
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time


# CreatePath should take a start and end position, and optionally a 
# list of positions to avoid
class Plot:
    def __init__(self) :
            # create the fogure and axes
            self.fig_handle, self.ax = plt.subplots(1, 2, figsize=(20,10))
        
    def plot_paths(self, robots, map, optimal_paths):   
        
        # create empty list of platforms for setting axis limits
        # create list of 2 empty lists 
        platforms = [[], []]

       
        # get stationary robot position 
        stat_robot = robots.get_stat_robot()
        stat_robot_pos = stat_robot.position
        # plot hexagon at stat_robot_pos
        for a in range(2):
            platforms[a].append(stat_robot_pos)
            draw_platform(map, stat_robot_pos, self.ax[a], color='b')

        # get moving robot positions
        moving_robots = robots.get_moving_robots()
        mov_colors = [['r', 'g'], ['tab:red', 'tab:green']]
        # plot hexagons at moving robot positions
        for a in range(2):
            c_ind = 0
            for key, r in moving_robots.members.items():
                platforms[a].append(r.position)        
                draw_platform(map, r.position, self.ax[a], color=mov_colors[a][c_ind])
                c_ind += 1

        # plot optimal paths in second subplot
        c_ind = 0
        for key, path in optimal_paths.items():
            color=mov_colors[0][c_ind]
            c_ind += 1
            for p in path:
                platforms[1].append(p)
                draw_platform(map, p, self.ax[1], color=color)

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
                        draw_platform(map, p, self.ax[a], color='w') 

        # set axis limits
        for a in self.ax:
            a.set_xlim(x_min-1, x_max+1)
            a.set_ylim(y_min-1, y_max+1)

            #  flip y axis
            a.invert_yaxis()

            # make x and y axis scales equal
            a.set_aspect('equal')

            for t in a.texts:
                t.set_clip_on(True)

        # fig.canvas.manager.window.wm_geometry("800x600+0+0")
        # fig.canvas.manager.window.wm_attributes('-topmost', 1)

        self.fig_handle.canvas.manager.window.move(200, 100)

        self.fig_handle.canvas.flush_events()
        plt.show(block=False)
        time.sleep(2)
        return 

    def close_paths_plot(self):
        plt.close(self.fig_handle)

def draw_platform(map, pos, ax, color='r'):
    ''' draws a platform on the map '''

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
    # __package__ = "honeycomb_task"
    # directory = '/media/jake/LaCie/robot_maze_workspace'
    # directory = 'D:/testFolder/pico_robots/map'
    directory = 'C:/Users/Jake/Documents/robot_maze'
    # directory = 'C:/Users/Jake/Desktop/map_of_platforms'
    # map = platform_map.open_map(map='restricted_map', directory=directory)
    
    map = Map(directory=directory)
    map.goal_position = 146

    from robot import Robot, Robots 

    robot1 = Robot(1, '192.168.0.102', 65535, 155, 0, 'stationary', map)
    robot2 = Robot(2, '192.168.0.103', 65534, 136, 180, 'moving', map)
    robot3 = Robot(3, '192.168.0.104', 65533, 127, 300, 'moving', map)

   
    robots = Robots()
    robots.add_robots([robot1, robot2, robot3])
    # yaml_dir = 'D:/testFolder/pico_robots/yaml'
    # robots = Robots.from_yaml(yaml_dir)


    # next_plats = [43, 61]    
    # initial_positions = get_starting_positions(robots, map)
    # paths = get_all_paths(robots, next_plats, map)
    # optimal_paths = select_optimal_paths(paths, robots, next_plats, map)
    # print(optimal_paths)


    next_plats = get_next_positions(robots, map, None, 'hard')
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