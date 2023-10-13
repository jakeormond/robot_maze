import socket
import threading
import queue
import time

# Define constants
BUFFER_SIZE = 1024
TIMEOUT = 10
# NUM_COMMANDS = 2    

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

            time.sleep(0.1) # not sure if this necessary or not

    # print received data
    print(received_data)

    return received_data
            

def handle_server(robot, string_input, data_queue):
    
    server_address = (robot.ip_address, robot.port)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    bytes_to_send = bytes(string_input, 'utf8')

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
    max_retries = 3
    base_delay = 1  # Initial delay in seconds
    retry_counter = 0
    while True:        
        
        try:
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

        except ConnectionResetError:
            if retry_counter > max_retries:
                break
           
            # handle the exception (e.g. log an error message)
            time.sleep(base_delay * (2**retry_counter))  # wait a bit            
            retry_counter += 1

        time.sleep(0.1) # not sure if this necessary or not

    data_with_identifier = {'robot_id': robot.id, 
                            'data': received_data}

    data_queue.put(data_with_identifier)

    return

def send_over_sockets_serial(robots, paths, ordered_keys):
    # get commands
    commands = paths.command_strings
    # get robot keys
    robot_keys = list(commands.keys())                  

    data_queue = queue.Queue() # to collect the decoded data from handle_server

    NUM_COMMANDS = 3

    for c in range(NUM_COMMANDS):
        for key in ordered_keys:
            handle_server(robots.members[key], 
                          commands[key][c], data_queue)
        
        while not data_queue.empty():
            data = data_queue.get()
            print(data)
            print("Received:", data)

    return 

def send_over_sockets_threads(robots, paths, print_output=False):
     # get commands
    commands = paths.command_strings
    # get robot keys
    robot_keys = list(commands.keys())                  

    data_queue = queue.Queue() # to collect the decoded data from handle_server

    num_commands = len(commands[robot_keys[0]]) # both robots should have same number of commands

    for c in range(num_commands):
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
            # print(data)
            if print_output:
                 print("Received:", data)

            time.sleep(0.1)
    
    # robots.update_positions(paths)    
    return 
