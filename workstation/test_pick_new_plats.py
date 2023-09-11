import numpy as np
import pandas as pd
import datetime as dt
import platform_map as pm
import create_path as cp
import choices_class as cc
import robot_class as rc

if __name__ == '__main__':
    choices = cc.Choices()
    choices.start_choice(91)
    choices.register_choice(81, 101)

    choices.start_choice(101)
    choices.register_choice(111, 110)

    choices.start_choice(111)
    choices.register_choice(101, 120)

    choices.start_choice(101)
    choices.register_choice(91, 92)

    choices.start_choice(91)
    choices.register_choice(101, 82)

    choices.start_choice(101)
    choices.register_choice(111, 110)

    robot1 = rc.Robot(1, '192.100.0.101', 1025, 101, 0, 'moving', map)
    robot2 = rc.Robot(2, '192.100.0.102', 1026, 110, 0, 'moving', map)
    robot3 = rc.Robot(3, '192.100.0.103', 1027, 111, 0, 'stationary', map)

    robots = rc.Robots()
    robots.add_robots([robot1, robot2, robot3])

    directory = 'C:/Users/Jake/Desktop/map_of_platforms'
    map = pm.Map(directory=directory)

    next_pos = cp.get_next_positions(robots, map, choices, 'easy')