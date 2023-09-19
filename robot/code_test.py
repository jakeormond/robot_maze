import network
from network import WLAN
import socket
from time import sleep
import machine
from machine import Pin
import open_socket
import drive_robot as dr

online_flag = dr.check_online()
print(online_flag)
# dr.find_line_half_on(1)

dr.find_line_back_and_forth()
