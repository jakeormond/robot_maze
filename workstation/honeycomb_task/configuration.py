'''
create and read the configuration settings necessary to initialize
communication with the robots.
'''

import os 
import yaml

def create_yaml():

    data = {
        'robot1': {
            'robot_id': 1, 
            'ip_address': '192.168.0.102',
            'port': 65533,
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
            'port': 65535,
            'position': 0,
            'orientation': 0
        }
    }
    return data

def save_yaml(data, yaml_dir=None):
    if yaml_dir is None:
        # yaml_dir = '/media/jake/LaCie/robot_maze_workspace'
        yaml_dir = 'D:/testFolder/platform_maps_and_yaml/yaml'
    os.chdir(yaml_dir)

    with open('config.yaml', 'w') as yaml_file:
        yaml.dump(data, yaml_file, default_flow_style=False)

def read_yaml(yaml_dir):
    # yaml_dir = '/media/jake/LaCie/robot_maze_workspace'
    yaml_path = os.path.join(yaml_dir, 'config.yaml')
    
    with open(yaml_path) as yaml_file:
        data = yaml.load(yaml_file, Loader=yaml.FullLoader)
    
    return data

if __name__ == '__main__':
    configuration = create_yaml()

    yaml_dir = '/home/jake/Documents/robot_test_folder'
    save_yaml(configuration, yaml_dir)