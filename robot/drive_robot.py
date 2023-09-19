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
MAX_TURN_SPEED = 30
MIN_SPEED = 20
TYPICAL_TURN_DIST = 120
MAX_TURN_DIST = 145

DIST_TURN = 120 # this will need adjusting
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

def calculate_distance_straight(enc1_a, enc2_a):
    # read encoders, and calculate distance turned since last line
    enc1_b, enc2_b = read_encoders(ADDRESS, ENCODERONE)    
    encoder_distance1 = enc1_b - enc1_a
    encoder_distance2 = enc2_b - enc2_a
    return encoder_distance1, encoder_distance2


def calculate_distance_turn(enc1_a, enc2_a, direction):
    # read encoders, and calculate distance turned since last line
    enc1_b, enc2_b = read_encoders(ADDRESS, ENCODERONE)
   
    if direction == 1:
        encoder_distance1 = enc1_b - enc1_a
        if enc2_b == 0:
            encoder_distance2 = 0
        elif enc2_a > enc2_b:
            encoder_distance2 = enc2_a - enc2_b
        else:
            encoder_distance2 = 2**32 - enc2_b + enc2_a
        
    else:
        if enc1_b == 0:
            encoder_distance1 = 0
        elif enc1_a > enc1_b:
            encoder_distance1 = enc1_a - enc1_b
        else:
            encoder_distance1 = 2**32 - enc1_b + enc1_a
        encoder_distance2 = enc2_b - enc2_a
    
    return encoder_distance1, encoder_distance2

def read_sensors():
    val1 = adc1.read_u16() # IR sensor 1
    val2 = adc2.read_u16() # IR sensor 2
    # print(val1, val2)
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


def drive_straight(val1, val2, speed1, speed2): # drive straight along line, adjusting speed as necessary to stay on line          
    if val1 >= IR_THRESHOLD and val2 < IR_THRESHOLD:
        speed1 = round(speed1*0.5)
        
    elif val1 < IR_THRESHOLD and val2 >= IR_THRESHOLD:
        speed2 = round(speed2*0.5)
        
    else:
        speed1 = max(speed1, speed2)
        speed2 = speed1
        
    drive_basic(speed1, speed2)
    return speed1, speed2

def drive_forward_by_distance(distance, conn):
    conn.sendall('FWD DISTANCE = ' + str(distance) + ',')
    reset_encoders()
    enc1_a, enc2_a = read_encoders(ADDRESS, ENCODERONE)
    
    counter = 0
    while True:
        counter += 1
        # if counter%100 == 0:  
            # conn.sendall('DRIVE FWD BY DISTANCE LOOP ' + str(counter) + ',')
        drive_basic(10, 10)
        utime.sleep_ms(10)
        
        enc1_b, enc2_b = read_encoders(ADDRESS, ENCODERONE)
        encoder_distance1 = enc1_b - enc1_a
        encoder_distance2 = enc2_b - enc2_a
        
        conn.sendall('ENCODER DISTANCE =  ' + str(min(encoder_distance1, encoder_distance2)) + ',')
        
        if (min(encoder_distance1, encoder_distance2) >= distance) or (min(encoder_distance1, encoder_distance2) < 0):
            break
        
    drive_basic(0, 0)
    return max(encoder_distance1, encoder_distance2)

def find_line_half_on(sensor): # to move the second sensor over line when one sensor already over
    # first, make sure we're not already on the line
    online_flag = check_online()
    if online_flag == 3:
        print('we''re already on the line!')
        return 
        
    if sensor == 1:
        direction = -1
    else:
        direction = 1
    
    l_speed = r_speed = round(INITIAL_TURN_SPEED)
    if direction == 1:
        r_speed = -r_speed
    else:
        l_speed = -l_speed
        
    while True:
        drive_basic(l_speed, r_speed)
        utime.sleep_ms(20)  
        # check sensors
        online_flag = check_online()
        print(online_flag)
        
        if online_flag == 3:
            # found the line
            # conn.sendall('found line!,')
            print('found')
            break
        
        elif online_flag == 0:
            # conn.sendall('lost the line!,')
            print('not found')
            break
    
    drive_basic(0, 0)
    return

def find_line_back_and_forth():
    # first, make sure we're not already on the line
    online_flag = check_online()
    if online_flag != 0:
        print('we''re already on the line!')
        return
    
    direction = 1    
    init_dist = 10
    reset_encoders()
    enc1, enc2 = read_encoders(ADDRESS, ENCODERONE)
    
    counter = 0
    while True:
        if counter == 0:
            distance = init_dist/2
        elif counter == 1:
            distance = init_dist
               
        # drive and sleep
        drive_for_turn(INITIAL_TURN_SPEED, direction)            
        utime.sleep_ms(20)        
        
        # check if online
        online_flag = check_online()
        if online_flag == 3:
            print('found the line')
            drive_basic(0, 0)
            return
               
        # get distance turned
        distance1, distance2 = calculate_distance_turn(enc1, enc2, direction)
        print(distance1, distance2)
        
        if max(distance1, distance2) >= distance:
            print('change direction')
            drive_basic(0, 0)
            direction = -direction
            counter += 1
            
            reset_encoders()
            enc1, enc2 = read_encoders(ADDRESS, ENCODERONE)
            
            if counter%2 == 0:
                distance += 5
    
    

def initialize_for_drive(conn):
    # reset encoders
    reset_encoders()
    
    # read sensors to verify we are on a line
    val1, val2 = read_sensors()
    
    # read initial state of sensors, returning if robot not on line
    if val1 < IR_THRESHOLD and val2 < IR_THRESHOLD:
        # robot is not on the line!
        print('robot is not on the line!')
        conn.sendall('robot is not on the line!')
        online = False
    else:    
        print('robot is on the line')
        conn.sendall('robot is on the line,')
        online = True
    return online, val1, val2

def linear_drive(n_lines, conn):
    conn.sendall('LINEAR DRIVE,') 
    online, val1, val2 = initialize_for_drive(conn)
    if not online:
        return [-1], [-1], [-1], [-1]
        
    # initialize list of line distances
    line_distances1 = []
    line_distances2 = []
    
    gap_distances1 = []
    gap_distances2 = []
    
    # get initial encoder readings
    enc1_a, enc2_a = read_encoders(ADDRESS, ENCODERONE)
    
    # set initial speeds
    speed1 = 15
    speed2 = speed1
    
    # initialize line counter
    lines_traversed = 0
    
    # get start time
    start_time = time.time()   
    
    # main loop
    counter = 0
    while True:
        counter += 1
        if counter%10 == 0:  
            conn.sendall('LINEAR DRIVE - LOOP ' + str(counter) + ',')
        # drive and sleep
        round_speed1 = round(speed1)
        round_speed2 = round(speed2)
        drive_straight(val1, val2, round_speed1, round_speed2)                    
        utime.sleep_ms(10)
        
        # calculate elapsed time and stop if timed out
        elapsed_time = time.time() - start_time
        # conn.sendall(str(elapsed_time))
        if elapsed_time > 4:
            print('timed out')
            conn.sendall('timed out,')
            drive_basic(0, 0)
            return [-1], [-1],[-1], [-1]                 
        
        # read encoders, and calculate distance travelled since last marker
        enc1_b, enc2_b = read_encoders(ADDRESS, ENCODERONE)
       
        encoder_distance1 = enc1_b - enc1_a
        encoder_distance2 = enc2_b - enc2_a            
                    
        # accelerate or decelerate depending on how far robot's turned
        if (lines_traversed >= (n_lines-1)) and not online:  
            if max(speed1, speed2) > MIN_SPEED:  # decelerate
                conn.sendall('decelerating - lines_traversed =  ' + str(lines_traversed) + ',')
                speed1 -= .3
                speed2 -= .3
        
        elif max(speed1, speed2) < TOP_SPEED:  # accelerate
            speed1 += .3
            speed2 += .3
               
        # read sensors and update online
        val1, val2 = read_sensors()
        
        if (val1 > IR_THRESHOLD or val2 > IR_THRESHOLD) and not online:
            lines_traversed += 1
            gap_distances1.append(encoder_distance1)
            gap_distances2.append(encoder_distance2)
            
            reset_encoders()
            enc1_a, enc2_a = read_encoders(ADDRESS, ENCODERONE)
            
            conn.sendall('back on the line,')
            
            if lines_traversed == n_lines:          
                conn.sendall('breaking,')
                drive_basic(0, 0)
                break
            
            else:
                online = True
            
        elif (val1 < IR_THRESHOLD and val2 < IR_THRESHOLD) and online:
            line_distances1.append(encoder_distance1)
            line_distances2.append(encoder_distance2)
            
            reset_encoders()
            enc1_a, enc2_a = read_encoders(ADDRESS, ENCODERONE)
            
            conn.sendall('off the line,')
            online = False
        
    return line_distances1, line_distances2, gap_distances1, gap_distances2
   


def turn_in_place(n_lines, conn):
    
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
        conn.sendall('on the line,')
        return 0
    
    elif online_flag == 1: # get centred by turning slightly to the right
        sensor = 1
        find_line_half_on(sensor, conn)
    
    elif online_flag == 2: # get centred by turning slightly to the left
        sensor = 2
        find_line_half_on(sensor, conn)

    elif online_flag == 3: # need to find the line
        # move forward slightly
        drive_forward_by_distance(20, conn)
        # then search back and forth for the line
        find_line_back_and_forth()

    
    # find line
    # Step 1, move forward by a small amount
    
    


def turn_by_distance(distance, direction, conn): # direction == 1 for clockwise, -1 for counterclockwise
    
    conn.sendall('TURN_BY_DIST,')
         
    # reset encoders
    reset_encoders()
    enc1_a, enc2_a = read_encoders(ADDRESS, ENCODERONE)

    # set initial speeds, taking into account direction
    speed = INITIAL_TURN_SPEED
    
    # get start time
    start_time = time.time()   

    # main loop
    counter = 0
    while True:
        counter += 1
        
        encoder_distance1, encoder_distance2 = calculate_distance_turn(enc1_a, enc2_a, direction)
        
        if min(encoder_distance1, encoder_distance2) < (distance - 100):
            if speed < MAX_TURN_SPEED:
                # accelerate
                speed += 1
            
        elif speed > INITIAL_TURN_SPEED:
            # decelerate
            speed -= 1            
        
        if min(encoder_distance1, encoder_distance2) > distance:
            drive_basic(0, 0)
            break
          
        
        round_speed = round(speed)
        if direction == 1:
            drive_basic(round_speed, -round_speed)
        else:
            drive_basic(-round_speed, round_speed)
            
        utime.sleep_ms(20)        
            
        # calculate elapsed time and stop if timed out
        elapsed_time = time.time() - start_time
        # conn.sendall(str(elapsed_time))
        if elapsed_time > 4:
            print('timed out')
            conn.sendall('timed out,')
            conn.sendall('enc distance1 = ' + str(encoder_distance1) + ' enc distance2 = ' + str(encoder_distance2) + ',')
            drive_basic(0, 0)
            return [-1], [-1]                  
                       
    return 0, 0


