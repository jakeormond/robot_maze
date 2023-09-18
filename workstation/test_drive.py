import socket
from send_over_socket import send_over_socket

# send_over_socket('99, 3, 1, 4, 1, 2, 1', "192.168.0.102", 65535)    
send_over_socket('97', "192.168.0.102", 65535)    
#send_over_socket('99, 3', "192.168.0.103", 65534)    
#send_over_socket('99, 3', "192.168.0.104", 65533) 

