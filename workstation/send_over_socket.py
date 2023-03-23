# send_over_socket.py

def send_over_socket():
    import socket

    HOST = "192.168.0.102"  # The server's hostname or IP address (i.e. the pi pico w)
    PORT = 65535  # The port used by the server

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        # s.sendall(b"Hell, world")
        s.sendall(b'[97]')
        data = s.recv(1024)

    print(f"Received {data!r}")
    print(data)