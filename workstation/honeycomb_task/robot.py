''' 
Define the robot class. These instances will be used to represent the robots in 
the workstation control program. 
They should contain the following attributes: 1) the robot's ID, 2) the robot's 
ip address, 3) the robot's current position, 4) the robot's current orientation.
They should also contain the following methods: 1) a method to set the robot's
new position, 2) a method to set the robot's new orientation, 3) a method to
send a command to the robot and receive data from it (note that this method 
may ultimately be implemented independently of the robot class to deal with 
multiple robots at once)
'''
import sys
sys.path.append('/home/jake/Documents/robot_maze/workstation')

from honeycomb_task.configuration import read_yaml
import copy


# robot definition
class Robot:
    def __init__(self, robot_id, ip_address, port_number, position, orientation, state):
        self.id = robot_id
        self.ip_address = ip_address
        self.port = port_number        
        self.position = position
        self.orientation = orientation # 0, 60, 120, 180, 240, 300
        self.state = state # stationary or moving

    @classmethod
    def from_yaml(cls, robot_id, yaml_data):
        ip_address = yaml_data[f"robot{robot_id}"]['ip_address']
        port_number = yaml_data[f"robot{robot_id}"]['port']
        position = None
        orientation = None
        state = 'stationary'
        return cls(robot_id, ip_address, port_number, position, orientation, state)

    def set_new_position(self, new_position):
        self.position = new_position
    
    def set_new_orientation(self, new_orientation):
        self.orientation = new_orientation

    def set_new_state(self, new_state):
        self.state = new_state

    def __str__(self):
        return (
            f'Robot {self.id} at {self.ip_address}, port {self.port} '
            f'is at position {self.position} and orientation {self.orientation},'
            f' and in the {self.state} state.'
        )

class Robots:
    def __init__(self, *args):
        self.members = {}

        for robot in args:
            self.add_robot(robot)

    @classmethod
    def from_yaml(cls, yaml_dir, positions=None, orientations=None, robot_ids=None):
        robots = Robots()        
        robot_dict = read_yaml(yaml_dir)
        # loop through the dictionary
        if robot_ids is None:
            robot_ids = []
            for key, value in robot_dict.items():
                robot_id = value['robot_id']
                robot = Robot.from_yaml(robot_id, robot_dict)
                
                if key != 'robot1':
                    robot.set_new_state('moving')
                
                robots.add_robot(robot)

                robot_ids.append(robot_id)

        else:
            for robot_id in robot_ids:
                robot = Robot.from_yaml(robot_id, robot_dict)
                robots.add_robot(robot)
    
        
        for i, id in enumerate(robot_ids):
            if positions is None:
                robots.members[f'robot{id}'].\
                        set_new_position(int(input(f'Robot {id} - Enter new position: ')))
            else:
                robots.members[f'robot{id}'].\
                        set_new_position(positions[i])
            
            if orientations is None:       
                robots.members[f'robot{id}'].\
                        set_new_orientation(int(input(f'Robot {id} - Enter new orientation (0, 60, 120, 180, 240, 300): ')))
            else:
                robots.members[f'robot{id}'].\
                        set_new_orientation(orientations[i])

        return robots       

    def add_robot(self, robot):
        self.members[f'robot{robot.id}'] = robot   

    def add_robots(self, robot_list):
        for robot in robot_list:
            self.add_robot(robot)
       
    def get_positions(self):
        positions = []
        for r in self.members:
            positions.append(self.members[r].position)
        return positions
    
    def get_orientations(self):
        orientations = []
        for r in self.members:
            orientations.append(self.members[r].orientation)
        return orientations

    def get_stat_robot(self):
        # check how many robots are stationary
        n_stationary = 0
        for r in self.members:
            if self.members[r].state == 'stationary':
                n_stationary += 1
        if n_stationary != 1:
            print(f'found {n_stationary} stationary robots, should be 1')
            return n_stationary

        for r in self.members:
            if self.members[r].state == 'stationary':
                return self.members[r]
            
    def get_moving_robots(self): # this returns a dictionary in some early code, so may need to fix
        moving_robots = copy.deepcopy(self)
        for r in self.members:
            if self.members[r].state == 'stationary':
                moving_robots.members.pop(r)
        return moving_robots
    
    def get_robot(self, robot_id):
        return self.members[f'robot{robot_id}']
    
    def get_robot_ids(self):
        return list[self.members.keys()]
    
    def update_positions(self, paths):
        for r in paths.optimal_paths:
            self.members[r].set_new_position(paths.optimal_paths[r][-1])
            self.members[r].set_new_orientation(paths.orientations[r][-1][-1])
        
        stat_robot = self.get_stat_robot()
        start_platform = stat_robot.position
        
        positions = self.get_positions()

        return start_platform, positions
    
    def update_positions_v2(self, paths):
        for r in paths.optimal_paths:
            self.members[r].set_new_position(paths.optimal_paths[r][-1])
            self.members[r].set_new_orientation(paths.orientations[r][-1][-1])

    
    def update_orientations(self, initial_turns):
        for r in initial_turns.optimal_paths:
            self.members[r].set_new_orientation(initial_turns.orientations[r][-1][-1])
        
        stat_robot = self.get_stat_robot()
        start_platform = stat_robot.position
        
        positions = self.get_positions()

        return start_platform, positions

    def get_robot_key_at_position(self, position):
        for key, robot in self.members.items():
            if robot.position == position:
                return key
    
    def __str__(self):
        for r in self.members:
            print(self.members[r])
        return ''


def get_robot_positions(robots):
    # get the positions of the robots from the dict of robot objects.
    robot_positions = []
    for r in range(3):
        robot_positions.append(robots.members[f'robot{r+1}'].position)
    return robot_positions


if __name__ == '__main__':
    # directory = 'D:/testFolder/pico_robots/map'
    directory = 'C:/Users/Jake/Documents/robot_maze/python_code/robot_maze/workstation/map_files'
    from platform_map import Map
    map = Map(directory=directory)

    robot1 = Robot(1, '192.100.0.101', 1025, 61, 0, 'stationary', map)
    robot2 = Robot(2, '192.100.0.102', 1026, 70, 0, 'moving', map)
    robot3 = Robot(3, '192.100.0.103', 1027, 71, 0, 'moving', map)

    robots = Robots()
    robots.add_robots([robot1, robot2, robot3])
    print(robots)
    