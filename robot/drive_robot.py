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
MAX_TURN_SPEED = 30
MIN_SPEED = 20
TYPICAL_TURN_DIST = 120
MAX_TURN_DIST = 145

DIST_TURN = 1000 # this will need adjusting
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
    # print(enc1,enc2)

def read_encoders(ADDRESS, ENCODERONE):
    readBuffer = i2c.readfrom_mem(ADDRESS, ENCODERONE, 8)
    enc1 = (readBuffer[0]<<24) + (readBuffer[1]<<16) + (readBuffer[2]<<8) + readBuffer[3]
    enc2 = (readBuffer[4]<<24) + (readBuffer[5]<<16) + (readBuffer[6]<<8) + readBuffer[7]
    return enc1, enc2

def read_sensors():
    val1 = adc1.read_u16() # IR sensor 1
    val2 = adc2.read_u16() # IR sensor 2
    # print(val1, val2)
    return val1, val2

def drive_basic(speed1, speed2):  # for turning or driving with no line    
    set_speed(speed1, SPEED1, speed2, SPEED2, writeBuffer, ADDRESS)  
    return 0

def drive_straight_for_time(speed1, speed2, time_limit): # for testing
    start_time = time.time()
    last_elapsed_time = 0
    sleep_counter = 0
    while True:
        drive_basic(speed1, speed2)
        
        utime.sleep_ms(5)
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

def drive_forward_by_distance(distance):
    reset_encoders()
    enc1_a, enc2_a = read_encoders(ADDRESS, ENCODERONE)
    
    while True:
        drive_basic(10, 10)
        utime.sleep_ms(5)
        
        enc1_b, enc2_b = read_encoders(ADDRESS, ENCODERONE)
        encoder_distance1 = enc1_b - enc1_a
        encoder_distance2 = enc2_b - enc2_a
        
        if min(encoder_distance1, encoder_distance2) >= distance:
            break
        
    drive_basic(0, 0)
    return max(encoder_distance1, encoder_distance2)

def find_line(direction, conn):
    reset_encoders()
    enc1_a, enc2_a = read_encoders(ADDRESS, ENCODERONE)
    
    speed = MIN_SPEED
    
    while True:
        # turn
        if direction == 1:
            drive_basic(speed, -speed)
        else:
            drive_basic(-speed, speed)
        
        print(f'speed = {speed}')
        utime.sleep_ms(5)
        
        # check sensors
        val1, val2 = read_sensors()
        # print(val1, val2)
    
        # read initial state of sensors, returning if robot not on line
        if val1 > IR_THRESHOLD and val2 > IR_THRESHOLD:
            found_flag = True
            drive_basic(0, 0)            
            conn.sendall('found line,')
            return found_flag
        
        # calculate distance turned, and exit if too far
        enc1_b, enc2_b = read_encoders(ADDRESS, ENCODERONE)
        
        if direction == 1:
            encoder_distance1 = enc1_b - enc1_a
            encoder_distance2 = 2**32 - enc2_b
            
        else:
            encoder_distance1 = 2**32 - enc1_b
            encoder_distance2 = enc2_b - enc2_a
        
        print(encoder_distance1, encoder_distance2)
        # print(enc1_a, enc1_b, enc2_a, enc2_b)
        
        if min(encoder_distance1, encoder_distance2) >= MAX_TURN_DIST:
            found_flag = False
            conn.sendall('didn''t find line,')
            drive_basic(0, 0)    
            return found_flag
        

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
    while True:
        # drive and sleep
        round_speed1 = round(speed1)
        round_speed2 = round(speed2)
        drive_straight(val1, val2, round_speed1, round_speed2)                    
        utime.sleep_ms(5)
        
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
   

def turn_in_place(n_lines, conn): # direction == 1 for clockwise, -1 for counterclockwise
    # set direction
    if n_lines <= 3:
        direction = 1
    else:
        n_lines = 6 - n_lines
        direction = -1
    
    # initialize list of line distances
    line_distances1 = []
    line_distances2 = []
    
    # read sensors to verify we are on a line
    val1, val2 = read_sensors()

    # read initial state of sensors, returning if robot not on line
    if val1 < IR_THRESHOLD and val2 < IR_THRESHOLD:
        # robot is not on the line!
        print('robot is not on the line!')
        conn.sendall('robot is not on the line!')
        online = False
        return [0], [0]
    
    print('robot is on the line')
    conn.sendall('robot is on the line,')
    online = True

    # reset encoders
    reset_encoders()
    enc1_a, enc2_a = read_encoders(ADDRESS, ENCODERONE)

    # set initial speeds, taking into account direction
    speed = 15
    
    # initialize line counter
    lines_turned = 0

    # get start time
    start_time = time.time()   

    # main loop
    while True:    
        # drive and sleep
        round_speed = round(speed)
        if direction == 1:
            drive_basic(round_speed, -round_speed)
        else:
            drive_basic(-round_speed, round_speed)
            
        utime.sleep_ms(5)        
            
        # calculate elapsed time and stop if timed out
        elapsed_time = time.time() - start_time
        # conn.sendall(str(elapsed_time))
        if elapsed_time > 10:
            print('timed out')
            conn.sendall('timed out,')
            drive_basic(0, 0)
            return [-1], [-1]                  

        # read encoders, and calculate distance turned since last line
        enc1_b, enc2_b = read_encoders(ADDRESS, ENCODERONE)
        if direction == 1:
            encoder_distance1 = enc1_b - enc1_a
            encoder_distance2 = 2**32 - enc2_b
            
        else:
            encoder_distance1 = 2**32 - enc1_b
            encoder_distance2 = enc2_b - enc2_a
            
        # accelerate or decelerate depending on how far robot's turned
        if (lines_turned < (n_lines-1)) or (min(encoder_distance1, encoder_distance2) < 50):  
            if speed < MAX_TURN_SPEED:  # accelerate
                speed += .3
                
        elif speed > MIN_SPEED:  # decelerate
            speed -= .3
            
        
        # read sensors 
        val1, val2 = read_sensors()
        
        # change online flag to False if was True and no longer on line
        if val1 < IR_THRESHOLD and val2 < IR_THRESHOLD:
            if online:
                print('gone off line')
                conn.sendall('gone off line,')
            
            online = False

        # if moved on to line, increment lines_turned
        elif val1 > IR_THRESHOLD and val2 > IR_THRESHOLD:       
            if not online:
                online = True
                lines_turned += 1
                print(f'lines turned : {lines_turned}')
                conn.sendall('lines turned : ' + str(lines_turned) + ',')   
                
                line_distances1.append(encoder_distance1)
                line_distances2.append(encoder_distance2)

                reset_encoders()
                enc1_a, enc2_a = read_encoders(ADDRESS, ENCODERONE)

        # if missed line, increment lines turned
        elif min(encoder_distance1, encoder_distance2) > MAX_TURN_DIST:
            online = True
            lines_turned += 1
            print(f'lines turned : {lines_turned}')
            conn.sendall('missed line, so incremented lines_turned,')  
            conn.sendall('lines turned : ' + str(lines_turned) + ',')   
            
            line_distances1.append(encoder_distance1)
            line_distances2.append(encoder_distance2)

            reset_encoders()
            enc1_a, enc2_a = read_encoders(ADDRESS, ENCODERONE)
            
            if lines_turned == n_lines: # we have missed the final line, so undoubtedly have turned too far
                # need to find the line: 1) drive forwards a bit, then 2) turn in opposite
                # direction until it is found.
                drive_forward_by_distance(20)
                found_flag = find_line(-direction, conn)
                
        if lines_turned == n_lines:
            conn.sendall('speed : ' + str(speed) + ',')
            
            conn.sendall('breaking,')
            drive_basic(0, 0)
            break
                
    return line_distances1, line_distances2
