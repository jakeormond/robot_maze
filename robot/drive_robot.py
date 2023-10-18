from machine import Pin, ADC, I2C
import time
import utime
import socket

# initialize emitter/collector
power1 = Pin(2, Pin.OUT)
power1.value(1)

power2 = Pin(3, Pin.OUT)
power2.value(1)

adc_pin1 = Pin(26)
adc_pin2 = Pin(27)

adc1 = ADC(adc_pin1)
adc2 = ADC(adc_pin2)

# initialize motors
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100_000)

# set reg addresses
SOFTWAREREG = 0x0D
SPEED1 = 0x00
SPEED2 = 0x01
VOLTREAD = 0x0A
ENCODERONE = 0x02
CMD = 0x10
RESETENCODERS = 0x20
MODE_REG = 0x0F

# set constants
IR_THRESHOLD = 7000 # probably needs adjusting
TOP_SPEED = 40  # 127
INITIAL_TURN_SPEED = 10
INITIAL_STRAIGHT_SPEED = 15
MAX_TURN_SPEED = 30
MIN_SPEED = 20

DIST_TURN = 115 # this will need adjusting
DIST_LINE = 2000
SLOWING_DIST = 500 # distance at which to start slowing
MODE = 1
ADDRESS = 0x58

writeBuffer=bytearray(2)

# set mode
writeBuffer[0] = MODE_REG
writeBuffer[1] = MODE
i2c.writeto(ADDRESS,writeBuffer)

# function for setting speed
def set_speed(speed1, SPEED1, speed2, SPEED2, writeBuffer, ADDRESS):
    writeBuffer[0] = SPEED1
    writeBuffer[1] = speed1
    i2c.writeto(ADDRESS,writeBuffer)

    writeBuffer[0] = SPEED2
    writeBuffer[1] = speed2
    i2c.writeto(ADDRESS,writeBuffer)

# function for reading encoders
def reset_encoders():
    writeBuffer[0] = CMD
    writeBuffer[1] = RESETENCODERS
    i2c.writeto(ADDRESS,writeBuffer)
    enc1, enc2 = read_encoders(ADDRESS, ENCODERONE)
    return enc1, enc2

def read_encoders(ADDRESS, ENCODERONE):
    readBuffer = i2c.readfrom_mem(ADDRESS, ENCODERONE, 8)
    enc1 = (readBuffer[0]<<24) + (readBuffer[1]<<16) + (readBuffer[2]<<8) + readBuffer[3]
    enc2 = (readBuffer[4]<<24) + (readBuffer[5]<<16) + (readBuffer[6]<<8) + readBuffer[7]
    return enc1, enc2

def send_msg_over_socket(message, conn):
    if conn != None:
        conn.sendall(message + ',')
    else:
        print('no socket, msg: ' + message)

def calculate_distance(enc1_a, enc2_a):
    # ignores direction and corrects for large encoder values due to rotation below zero.
    # assumes encoder values are not going to be huge (i.e. over 1000).
    # should be able to replace all other calculate_distance functions
    init_vals = [enc1_a, enc2_a]
    
    enc1_b, enc2_b = read_encoders(ADDRESS, ENCODERONE)
    new_encoder_vals = [enc1_b, enc2_b]
    
    distance = [None, None]
    
    for i, new_val in enumerate(new_encoder_vals):        
        if init_vals[i] < 100000:
            if new_val < 10000:
                distance[i] = abs(new_val - init_vals[i])
            else:
                distance[i] = init_vals[i] + (2**32 - new_val)
        else: # init_vals[i] >= 100000
            if new_val < 10000:
                distance[i] = new_val + (2**32 - init_vals[i])
            else: # new_val >= 10000
                distance[i] = abs(new_val - init_vals[i])
       
    return distance[0], distance[1]


def read_sensors():
    val1 = adc1.read_u16() # IR sensor 1
    val2 = adc2.read_u16() # IR sensor 2
    return val1, val2

def check_online(): # 0 not on line, 1 left on line, 2 right on line, 3 both on line
    val1, val2 = read_sensors()
    if (val1 < IR_THRESHOLD) and (val2 < IR_THRESHOLD):
        return 0
    elif (val1 >= IR_THRESHOLD) and (val2 < IR_THRESHOLD):
        return 1
    elif (val1 < IR_THRESHOLD) and (val2 >= IR_THRESHOLD):
        return 2
    elif (val1 >= IR_THRESHOLD) and (val2 >= IR_THRESHOLD):
        return 3
    else:
        return None

def drive_basic(speed1, speed2):  # for turning or driving with no line    
    set_speed(speed1, SPEED1, speed2, SPEED2, writeBuffer, ADDRESS)  
    return 0

def drive_for_turn(speed, direction):
    if direction == 1:
        drive_basic(speed, -speed)
    else:
        drive_basic(-speed, speed)
    return

def drive_straight_for_time(speed1, speed2, time_limit): # for testing
    start_time = time.time()
    last_elapsed_time = 0
    sleep_counter = 0
    while True:
        drive_basic(speed1, speed2)
        
        utime.sleep_ms(10)
        sleep_counter += 1
        
        elapsed_time = time.time() - start_time
        
        if elapsed_time >= time_limit:
            drive_basic(0, 0)
            print(f'stopping at time : {elapsed_time} sec')
            print(f'sleep_counter : {sleep_counter}')
            break
        
        if elapsed_time > last_elapsed_time:
            last_elapsed_time = elapsed_time
            print(f'elapsed time : {elapsed_time} sec')
            print(f'sleep_counter : {sleep_counter}')
            sleep_counter = 0
            
    return 0


def drive_straight(online_flag, speed1, speed2): # drive straight along line, adjusting speed as necessary to stay on line          
    if online_flag == 1:
        speed1 = round(speed1*0.6)
        
    elif online_flag == 2:
        speed2 = round(speed2*0.6)
        
    else:
        speed1 = max(speed1, speed2)
        speed2 = speed1
        
    drive_basic(speed1, speed2)
    return speed1, speed2

def drive_forward_by_distance(distance, conn=None):
    
    # send_msg_over_socket('FWD DISTANCE = ' + str(distance), conn)
    
    enc1_a, enc2_a = reset_encoders()
    
    counter = 0
    while True:
        counter += 1
        drive_basic(10, 10)
        utime.sleep_ms(10)
        
        encoder_distance1, encoder_distance2 = calculate_distance(enc1_a, enc2_a)
          
        if min(encoder_distance1, encoder_distance2) >= distance:
            break
        
    drive_basic(0, 0)
    return max(encoder_distance1, encoder_distance2)

def find_line_half_on(conn=None): # to move the second sensor over line when one sensor already over
    
    # send_msg_over_socket('find_line_half_on', conn)
        
    # first, make sure we're not already on the line
    online_flag = check_online()
    if online_flag == 3:
        # send_msg_over_socket('we''re already on the line!', conn)
        return
    
    if online_flag == 0:
        # send_msg_over_socket('not on line!', conn)
        return
        
        
    if online_flag == 1:
        direction = -1
    else:
        direction = 1   
        
    while True:
        drive_for_turn(INITIAL_TURN_SPEED, direction)
        utime.sleep_ms(20)  
        # check sensors
        online_flag = check_online()
        print(online_flag)
        
        if online_flag == 3:
            # found the line
            # send_msg_over_socket('found line!', conn)
            break
        
        elif online_flag == 0:
            # send_msg_over_socket('lost the line!', conn)
            break
    
    drive_basic(0, 0)
    return

def find_line_back_and_forth(conn=None):
    
    # send_msg_over_socket('find_line_back_and_forth', conn)
    
    # first, make sure we're not already on the line
    online_flag = check_online()
    if online_flag != 0:
        # send_msg_over_socket('we''re already on the line!', conn)
        return
    
    direction = 1    
    init_dist = 10
    enc1, enc2 = reset_encoders()
    
    counter = 0
    while True:
        if counter == 0:
            distance = init_dist/2
        elif counter == 1:
            distance = init_dist
               
        # drive and sleep
        drive_for_turn(INITIAL_TURN_SPEED, direction)            
        utime.sleep_ms(10)        
        
        # check if online
        online_flag = check_online()
        if online_flag != 0:
            # send_msg_over_socket('found the line', conn)
                        
            if online_flag != 3:
                find_line_half_on(conn)           
            
            break
                
        # get distance turned
        distance1, distance2 = calculate_distance(enc1, enc2)
                
        if max(distance1, distance2) >= distance:
            drive_basic(0, 0)
            utime.sleep_ms(100)      
            direction = -direction
            counter += 1
            
            if counter%2 == 0:
                drive_forward_by_distance(20)
            
            enc1, enc2 = reset_encoders()          
            distance += 10               
    
    drive_basic(0, 0)       
    return
    
def linear_drive(n_lines, conn=None):
    # line distance ~= 150, gap ~= 50
    
    # send_msg_over_socket('LINEAR DRIVE', conn) 
    
    if n_lines == 0:
        # send_msg_over_socket('n_lines = 0 so returning', conn)
        return [], [], [], []
       
    # check if over the line, and straighten out if necessary
    online_flag = check_online() # 0 not on line, 1 left sensor on line, 2 right sensor on line, 3 both sensors on line
    if online_flag == 0:
        # send_msg_over_socket('trying to find line', conn) 
        drive_forward_by_distance(40, conn)
        find_line_back_and_forth(conn)        
    
    elif online_flag != 3: # straighten out if both sensors not on line. 
        find_line_half_on(conn)
        online_flag = check_online()
        
    # initialize list of line distances
    line_distances1 = []
    line_distances2 = []
    
    gap_distances1 = []
    gap_distances2 = []
    
    # get initial encoder readings
    enc1, enc2 = reset_encoders()
    
    # set initial speeds
    speed1 = speed2 = INITIAL_STRAIGHT_SPEED
    
    # initialize line counter
    lines_traversed = 0
    
    # get start time
    start_time = time.time()   
    
    # main loop
    counter = 0
    online = True
    
    while True:
        counter += 1
               
        # drive and sleep
        round_speed1 = round(speed1)
        round_speed2 = round(speed2)
        drive_straight(online_flag, round_speed1, round_speed2)                    
        utime.sleep_ms(10)
        
        # calculate elapsed time and stop if timed out
        elapsed_time = time.time() - start_time
        # conn.sendall(str(elapsed_time))
        if elapsed_time > 10:
            print('timed out')
            conn.sendall('timed out,')
            drive_basic(0, 0)
            return [-1], [-1],[-1], [-1]                 
        
        # calculate distance travelled
        distance1, distance2 = calculate_distance(enc1, enc2)
                            
        # accelerate or decelerate depending on how far robot's turned
        if (lines_traversed >= (n_lines-1)) and not online:  
            if max(speed1, speed2) > MIN_SPEED:  # decelerate
                # send_msg_over_socket('decelerating - lines_traversed =  ' + str(lines_traversed), conn) 
                speed1 -= .3
                speed2 -= .3
        
        elif max(speed1, speed2) < TOP_SPEED:  # accelerate
            speed1 += .3
            speed2 += .3
        
        # check if online and update if necessary
        last_online_flag = online_flag
        online_flag = check_online()        
        if online_flag != 0 and not online and max(distance1, distance2) > 80:
            lines_traversed += 1
            online = True
            gap_distances1.append(distance1)
            gap_distances2.append(distance2)
            
            enc1, enc2 = reset_encoders()
            
            # send_msg_over_socket('back on the line', conn)
            
            if lines_traversed == n_lines:          
                # send_msg_over_socket('breaking', conn)
                drive_basic(0, 0)
                break
            
        elif online_flag == 0 and online and max(distance1, distance2) >= 150:
            online = False
            line_distances1.append(distance1)
            line_distances2.append(distance2)
            
            enc1, enc2 = reset_encoders()            
            
            # send_msg_over_socket('off the line', conn)
            
        elif online_flag == 0 and online and max(distance1, distance2) < 150:
            online_flag = last_online_flag          
            # send_msg_over_socket('off the line before gap - trying to find', conn)
        
    return line_distances1, line_distances2, gap_distances1, gap_distances2
   

def turn_in_place(n_lines, conn=None):
    
    send_msg_over_socket('TURN IN PLACE', conn)
    
    if n_lines == 0:
        send_msg_over_socket('n_lines = 0 so returning', conn)
        return 0, 0
    
    # first, turn by distance
    if n_lines <= 3:
        direction = 1
    else:
        n_lines = 6 - n_lines
        direction = -1
    
    distance = DIST_TURN * n_lines
    turn_by_distance(distance, direction, conn)
    
    # check if on line    
    online_flag = check_online() # 0 not on line, 1 left sensor on line, 2 right sensor on line, 3 both sensors on line
    if online_flag == 3: # on the line      
        send_msg_over_socket('on the line', conn)
    
    elif online_flag > 0: # get centred 
        send_msg_over_socket('half on', conn)
        find_line_half_on(conn)

    else: # if online_flag == 0
        send_msg_over_socket('not on line!', conn)
        # move forward slightly
        drive_forward_by_distance(20, conn)
        # then search back and forth for the line        
        find_line_back_and_forth(conn)
    
    send_msg_over_socket('finished turn_in_place', conn)
    return 0, 0


def turn_by_distance(distance, direction, conn=None): # direction == 1 for clockwise, -1 for counterclockwise
    # updated on Oct 5, 2023: now, the robot starts looking for the line at
    # some distance before the target distance, and stops if it finds it. 
    
    send_msg_over_socket('TURN_BY_DIST', conn)
         
    # reset encoders
    enc1, enc2 = reset_encoders()

    # set initial speeds, taking into account direction
    speed = INITIAL_TURN_SPEED
    
    # get start time
    start_time = time.time()   

    # main loop
    counter = 0
    
    # check if online
    last_flag = check_online()
    
    # set line counter
    line_count = 0
    
    while True:
        counter += 1
        
        distance1, distance2 = calculate_distance(enc1, enc2)
        
        # acceleration and deceleration
        if min(distance1, distance2) < (distance - 100):
            if speed < MAX_TURN_SPEED:
                # accelerate
                speed += 1
            
        elif speed > INITIAL_TURN_SPEED:
            # decelerate
            speed -= 1            
        
        # count the lines - we're not currently using this
        # count, but we may need to in the future. 
        online_flag = check_online()
        if online_flag == 0 and last_flag != 0:
            line_count += 1
            send_msg_over_socket(f'line_count = {line_count}', conn)
        last_flag = online_flag
        
        
        
        # look for the line at some distance before target -
        # we'll try 1/5 the inter-line distance to start
        if min(distance1, distance2) > (distance - int(1/5*(DIST_TURN))):
            online_flag = check_online()
            if online_flag == 3:
                drive_basic(0, 0)
                break
            
            elif direction == 1 and online_flag == 1:
                drive_basic(0, 0)
                break
        
            elif direction == -1 and online_flag == 2:
                drive_basic(0, 0)
                break
                    
        if min(distance1, distance2) > distance:
            drive_basic(0, 0)
            break          
        
        round_speed = round(speed)
        drive_for_turn(round_speed, direction)                   
        utime.sleep_ms(10)        
            
        # calculate elapsed time and stop if timed out
        elapsed_time = time.time() - start_time
        # conn.sendall(str(elapsed_time))
        if elapsed_time > 4:
            send_msg_over_socket('timed out', conn)
            
            drive_basic(0, 0)
            return -1, -1                  
                       
    return 0, 0


