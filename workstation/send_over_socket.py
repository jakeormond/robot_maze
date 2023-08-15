def send_over_socket(string_input):
    import socket

    HOST = "192.168.0.102"  # The server's hostname or IP address (i.e. the pi pico w)
    PORT = 65535  # The port used by the server

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
            

        
        