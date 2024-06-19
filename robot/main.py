import network
from network import WLAN
import socket
from time import sleep
import machine
from machine import Pin
import open_socket
from open_socket import connect


#ssid = 'TP-Link_6612'
#password = '39308399'

ssid = 'TP-Link_BD5D'
password = '31941976'

# ssid = 'TP-Link_B182'
# password = '35208877'

PORT = 65534 # robot 1 is 65535

ipconfig = ('192.168.0.103', '255.255.255.0', '192.168.0.1', '8.8.8.8')
# robot 1 is '192.168.0.102'

try:
    wlan = connect(ipconfig, ssid, password)
except KeyboardInterrupt:
    wlan = connect()

# open_socket.open_socket_connection()
    
open_socket.open_socket_connection(PORT, wlan, ipconfig, ssid, password)
