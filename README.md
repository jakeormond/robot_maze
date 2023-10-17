#Robot honeycomb maze

robot (raspberry pi pico w)
- main.py 
	- this makes the connection to the wifi router
	- once connected, it opens a socket connection by calling 
	open_socket.open_socket_connection()
- open_socket
	- opens socket (pi pico w led will turn on to inicate socket is open)
	- if it receives a ['3'] from the laptop, it calls irAndMotorsV3.drive()
- irAndMotors
	- functions for reading motor encoders, setting motor speeds, and driving 
	the motors


laptop
- send_over_socket.py
	- connects to router and sends a command (currently just '[3]') which tells
	the robot to run the motors. 	
