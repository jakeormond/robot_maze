import socket
import select
import threading
import queue

# Define constants
BUFFER_SIZE = 1024
TIMEOUT = 10
NUM_COMMANDS = 2    

def send_over_socket(string_input, HOST, PORT):
    import socket

    # HOST = "192.168.0.102"  # The server's hostname or IP address (i.e. the pi pico w)
    # PORT = 65535  # The port used by the server

    bytes_to_send = bytes(string_input, 'utf8')
    received_data = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        # s.sendall(b"Hell, world")
        s.sendall(bytes_to_send)
       
        counter = 0
        
        while True:
            counter += 1
            print('counter : ', counter)
            data = s.recv(1024)

            # check if data is empty
            if not data:
                break
            
            print(f"Received {data!r}")
            print(data)
            
            data = data.decode('utf8')
            # split data on comma
            data = data.split(',')
            # check is any elements are empty and remove them
            data = [x for x in data if x != '']

            # append to received data
            received_data.extend(data)

    # print received data
    print(received_data)

    return received_data
            

def send_over_sockets_select(robots, paths):
      
    # get commands
    commands = paths.command_strings
    # get robot keys
    robot_keys = list(commands.members.keys())                  

    # create a list of tuples containing each robots ip address and port
    server_address = [(robots.members[key].ip_address, robots[key].port) for key in robot_keys]

    for c in range(NUM_COMMANDS):
        # Create socket objects for each server
        sockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(len(robot_keys))]
        bytes_to_send = [bytes(commands[key][c], 'utf8') for key in robot_keys] 
        received_data = [[] for _ in range(len(robot_keys))]

        # Connect to each server
        for r, s in enumerate(sockets):
            try:
                    s.connect(server_address[r])
                    s.sendall(bytes_to_send[r])
            except (socket.error, ConnectionRefusedError) as e:
                print(f"Error connecting to {robot_keys[r]}: {e}")
                print("Try rebooting it and then press enter to continue")
                # pause the program while the user reboots the robot
                input(" ")

                try:
                    # try to connect again
                    s.connect(server_address[r])
                    s.sendall(bytes_to_send[r])
                except (socket.error, ConnectionRefusedError) as e:
                    print(f"Reconnection to  {robot_keys[r]} failed: {e}")
                    print("Aborting")
                    return
        
        while True:
            readable, _, _ = select.select(sockets, [], [], TIMEOUT)

            for r, s in enumerate(readable):
                data = s.recv(BUFFER_SIZE)

                # check if data is empty
                if not data:
                    s.close()
                    break
                
                print(f"Received {data!r}")
                print(data)
                
                data = data.decode('utf8')
                # split data on comma
                data = data.split(',')
                # check is any elements are empty and remove them
                data = [x for x in data if x != '']

                # append to received data
                received_data[r].extend(data)

    for s in sockets:
        s.close()
        
    for r, data in enumerate(received_data):
        print(f"Data from {robot_keys[r]}: " + data)
    
    return received_data


def handle_server(robot, bytes_to_send, data_queue):
    
    server_address = (robot.ip_address, robot.port)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.connect(server_address)
        s.sendall(bytes_to_send)
    except (socket.error, ConnectionRefusedError) as e:
        print(f"Error connecting to robot{robot.id}: {e}")
        print("Try rebooting it and then press enter to continue")
        # pause the program while the user reboots the robot
        input(" ")

        try:
            # try to connect again
            s.connect(server_address)
            s.sendall(bytes_to_send)
        except (socket.error, ConnectionRefusedError) as e:
            print(f"Reconnection to robot{robot.id} failed: {e}")
            print("Aborting")
            data_queue.put(f'Connection with robot{robot.id} failed')

            return 
   
    received_data = []
    while True:
        data = s.recv(BUFFER_SIZE)  # Receive data from server

        # check if data is empty
        if not data:
            break
            
        data = data.decode('utf8')
        # split data on comma
        data = data.split(',')
        # check is any elements are empty and remove them
        data = [x for x in data if x != '']
        received_data.extend(data)
    

    data_with_identifier = {'robot_id': robot.id, 
                            'data': received_data}

    data_queue.put(data_with_identifier)

    return


def send_over_sockets_threads(robots, paths):
     # get commands
    commands = paths.command_strings
    # get robot keys
    robot_keys = list(commands.members.keys())                  

    data_queue = queue.Queue() # to collect the decoded data from handle_server

    NUM_COMMANDS = 2

    for c in range(NUM_COMMANDS):
        threads = []
        for key in robot_keys:
            t = threading.Thread(target=handle_server, 
                                 args=(robots.members[key], 
                                commands[key][c], data_queue))
            
            t.start()
            threads.append(t)
        
        for thread in threads:
            thread.join()

        while not data_queue.empty():
            data = data_queue.get()
            print(data)
            print("Received:", data)

    return 


if __name__ == '__main__':
    import robot_class
    import create_path as cp
    import choices_class as cc

    robot1 = robot_class.Robot(1, '192.100.0.101', 1025, 72, 0, 'moving', map)
    robot2 = robot_class.Robot(2, '192.100.0.102', 1026, 81, 0, 'stationary', map)
    robot3 = robot_class.Robot(3, '192.100.0.103', 1027, 91, 0, 'moving', map)

    robots = robot_class.Robots()
    robots.add_robots([robot1, robot2, robot3])

    choices = cc.Choices()
    
    next_platforms = cp.get_next_positions(robots, map, choices,
                                            difficulty = 'hard')
    
    paths = cp.Paths(robots, next_platforms, map)

    send_over_sockets_threads(robots, paths)