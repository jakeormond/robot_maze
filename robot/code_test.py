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
# dr.find_line_half_on()

# dr.find_line_back_and_forth()
dr.turn_in_place(1)
# dr.linear_drive(3, conn=None)
# print(dr.read_sensors())

