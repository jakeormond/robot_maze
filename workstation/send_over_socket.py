def send_over_socket(string_input):
    import socket

    HOST = "192.168.0.102"  # The server's hostname or IP address (i.e. the pi pico w)
    PORT = 65535  # The port used by the server

    bytes_to_send = bytes(string_input, 'utf8')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        # s.sendall(b"Hell, world")
        s.sendall(bytes_to_send)
        data = s.recv(1024)

        print(f"Received {data!r}")
        print(data)
