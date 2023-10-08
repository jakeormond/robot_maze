'''
create yaml file with default settings for all 3 robots.
'''
import os
import yaml

data = {
    'robot1': {
        'robot_id': 1, 
        'ip_address': '192.168.0.102',
        'port': 65535,
        'position': 0,
        'orientation': 0
    },
    'robot2': {
        'robot_id': 2,
        'ip_address': '192.168.0.103',
        'port': 65534,
        'position': 0,
        'orientation': 0
    },
    'robot3': {
        'robot_id': 3,
        'ip_address': '192.168.0.104',
        'port': 65533,
        'position': 0,
        'orientation': 0
    }
}

# yaml_dir = '/media/jake/LaCie/robot_maze_workspace'
yaml_dir = 'D:/testFolder/pico_robots/yaml'
os.chdir(yaml_dir)

with open('config.yaml', 'w') as yaml_file:
    yaml.dump(data, yaml_file, default_flow_style=False)