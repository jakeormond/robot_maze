import sys 
import os

import unittest
from ..honeycomb_task import create_path
from ..honeycomb_task.robot import Robot, Robots
from ..honeycomb_task.platform_map import Map

class TestPaths(unittest.TestCase):

    def setUp(self):
        # initialize map
        self.map = Map(28, [9, 10]) 
        self.map.goal_position = 60
        
        
        # initialize robots
        robot_positions = [136, 145, 155]
        robot_orientations = [0, 180, 300]
        robot1 = Robot(1, 'some_number', 0, robot_positions[0], \
                       robot_orientations[0], 'stationary')
        robot2 = Robot(2, 'some_number', 1, robot_positions[1], \
                       robot_orientations[1], 'moving')
        robot3 = Robot(3, 'some_number', 2, robot_positions[2], \
                       robot_orientations[2], 'moving')
        
        self.robots = Robots()
        self.robots.add_robots([robot1, robot2, robot3])

        
    def tearDown(self) -> None:
        pass

    def test_optimal_paths(self):
        
        # initialize paths without specifying next_positions
        for _ in range(20):
            paths = create_path.Paths(self.robots, self.map)
            # paths.next_plats should include one of [117, 126, 127] since they are 
            # the only possible platforms closer to the goal
            contains_value = any(item in paths.next_plats for item in [117, 126, 127])
            self.assertTrue(contains_value, msg='next_plats does not contain one of [117, 126, 127]')

        # reinitialize paths with next_positions
        paths = create_path.Paths(self.robots, self.map, next_positions=[126, 127])
        robot2_path = [135, 126]
        self.assertListEqual(robot2_path, paths.optimal_paths['robot2'], msg='robot2_path is not [135, 126]')

        robot3_path = [165, 156, 137, 127]
        self.assertListEqual(robot3_path, paths.optimal_paths['robot3'], msg='robot3_path is not [165, 156, 137, 127]')


if __name__ == '__main__':
    unittest.main()