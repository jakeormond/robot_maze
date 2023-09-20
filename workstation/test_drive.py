import socket
from send_over_socket import send_over_socket

# send_over_socket('99, 0, 3, 3, 3', "192.168.0.102", 65535)    
# send_over_socket('94, 120, 1', "192.168.0.102", 65535)    
# send_over_socket('96, 40', "192.168.0.102", 65535)    
# send_over_socket('95, -1', "192.168.0.102", 65535)    
send_over_socket('97', "192.168.0.102", 65535)    
#send_over_socket('99, 3', "192.168.0.103", 65534)    
#send_over_socket('99, 3', "192.168.0.104", 65533) 

