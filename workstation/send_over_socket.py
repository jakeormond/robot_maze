import socket
import select
import threading
import queue

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

    NUM_COMMANDS = 2

    for c in range(NUM_COMMANDS):
        # Create socket objects for each server
        sockets = [socket.socket(socket.AF_INET, socket.SOCK_STREAM) for _ in range(len(robot_keys))]
        bytes_to_send = [bytes(commands[key][c], 'utf8') for key in robot_keys] 
        received_data = [[], []]

        # Connect to each server
        for r, s in enumerate(sockets):
            s.connect(server_address[s])
            s.sendall(bytes_to_send[s])
        
        while True:
            readable, _, _ = select.select(sockets, [], [], 10)

            for r, s in enumerate(readable):
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
                received_data[r].extend(data)
        
        for data in received_data:
            print(data)

def send_over_sockets_threads(robots, paths):
     # get commands
    commands = paths.command_strings
    # get robot keys
    robot_keys = list(commands.members.keys())                  

    # create a list of tuples containing each robots ip address and port
    server_addresses = [(robots.members[key].ip_address, robots[key].port) for key in robot_keys]

    data_queue = queue.Queue() # to collect the decoded data from handle_server

    NUM_COMMANDS = 2

    for c in range(NUM_COMMANDS):
        threads = []
        for address in server_addresses:
            t = threading.Thread(target=handle_server, args=(address,))
            t.start()
            threads.append(t)
        
        for thread in threads:
            thread.join()

        while not data_queue.empty():
            data = data_queue.get()
            print(data)
            print("Received:", data)


def handle_server(server_address, data_queue):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    
    received_data = []
    while True:
        data = sock.recv(1024)  # Receive data from server

        # check if data is empty
        if not data:
            break
            
        data = data.decode('utf8')
        # split data on comma
        data = data.split(',')
        # check is any elements are empty and remove them
        data = [x for x in data if x != '']
        received_data.extend(data)
    
    data_queue.put(received_data)




def parse_durations(robots, paths):
    durations = paths.durations
    durations_common = []

    # get the length of each entries in the durations dictionary
    # this is the number of commands to send to each robot
    num_commands = [len(durations[key]) for key in robot_keys]
    # code is only currently set to deal with 2 robots at a time
    if len(num_commands) != 2:
        raise ValueError('Code is only currently set to deal with 2 robots at a time')
    if num_commands[0] != num_commands[1]:
        raise ValueError('Number of commands to send to each robot must be equal')
    num_commands = num_commands[0]

    # get robot keys
    robot_keys = list(commands.members.keys())
    # keep max durations for each step
    for i in len(robot_keys):
        if i == 0:
            durations_common = durations[robot_keys[i]]
        else:
            for j in range(len(durations_common)):
                if durations_common[j] < durations[robot_keys[i]][j]:
                    durations_common[j] = durations[robot_keys[i]][j]   



if __name__ == '__main__':
    HOST = "192.168.0.102"  # The server's hostname or IP address (i.e. the pi pico w)
    PORT = 65535  # The port used by the server

    string_input = '1, 1, 1, 2, 1, 1'
    send_over_socket(string_input, HOST, PORT)