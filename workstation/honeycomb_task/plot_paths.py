'''
Defines a class that creates a path for the robot to follow, given a start
and end position.
It requires methods to create paths given certain constraints, such as
the shortest path, a path that avoids other robots or obstacles, etc.
'''
import numpy as np
from .platform_map import Map
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches


# CreatePath should take a start and end position, and optionally a 
# list of positions to avoid
class Plot:
    def __init__(self) :
            # create the fogure and axes
            self.fig_handle, self.ax = plt.subplots(1, 2, figsize=(10,5))
        
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

        self.fig_handle.canvas.manager.window.move(-1600, 200)

        self.fig_handle.canvas.flush_events()
        plt.show(block=False)
        plt.pause(2)
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
    # select a directory using tkinter
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    directory = filedialog.askdirectory()
    
    
    map = Map(directory=directory)
    map.goal_position = int(input('Enter goal position: '))

    from honeycomb_task.robot import Robots 
    yaml_dir = filedialog.askdirectory()
    robots = Robots.from_yaml(yaml_dir, orientations=[0, 0, 0])

    from honeycomb_task.create_path import Paths
    paths = Paths(robots, map)

    robot_path_plot = Plot()
    robot_path_plot.plot_paths(robots, map, paths.optimal_paths)

    # pause until user presses enter    
    input('Press enter to continue: ')
    
  