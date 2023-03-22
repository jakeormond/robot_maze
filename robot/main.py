import network
from network import WLAN
import socket
from time import sleep
import machine
from machine import Pin
import open_socket

def connect():
    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.ifconfig(ipconfig)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    led.value(True)

led = Pin('LED', Pin.OUT)
led.value(False)

#ssid = 'TP-Link_6612'
#password = '39308399'

ssid = 'TP-Link_BD5D'
password = '31941976'
PORT = 65535

ipconfig = ('192.168.0.102', '255.255.255.0', '192.168.0.1', '8.8.8.8')

try:
    connect()
except KeyboardInterrupt:
    machine.reset()

open_socket.open_socket_connection()
    
