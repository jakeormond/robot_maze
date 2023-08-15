from machine import Pin, ADC, I2C
import time
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
TOP_SPEED = 127
MIN_SPEED = 20
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

def drive_basic(speed1, speed2):    
    set_speed(speed1, SPEED1, speed2, SPEED2, writeBuffer, ADDRESS)  
    return 0

def drive_basic_for_time(speed1, speed2, time_limit):
    start_time = time.time()
    set_speed(speed1, SPEED1, speed2, SPEED2, writeBuffer, ADDRESS)
    while True:
        time2 = time.time()
        elapsed_time = time2 - start_time
        if elapsed_time > time_limit:
            break
    return 0


def drive_straight(val1, val2, speed): # drive straight along line, adjusting speed as necessary to stay on line          
    if val1 >= IR_THRESHOLD and val2 < IR_THRESHOLD:
        set_speed(speed, SPEED1, round(speed*0.95), SPEED2, writeBuffer, ADDRESS)
    
    elif val1 < IR_THRESHOLD and val2 >= IR_THRESHOLD:
        set_speed(round(speed*0.95), SPEED1, speed, SPEED2, writeBuffer, ADDRESS)
        
    else:
        set_speed(speed, SPEED1, speed, SPEED2, writeBuffer, ADDRESS)
    return 0

# get the distance in encoder units from one platform position to adjacent platforms
# for code development
def get_linear_distance():
    # reset encoders
    reset_encoders()

    # get initial IR values. Note that we are not yet set up for situation where somehow the robot is not on a line.
    val1, val2 = read_sensors()
    
    if val1 < IR_THRESHOLD and val2 < IR_THRESHOLD:
        # robot is not on the line!
        online = 0
        return 0, 0
    else:
        online = 1
    
    # set initial speed
    speed = TOP_SPEED

    start_time = time.time()
    while True:
        drive_straight(val1, val2, speed)
        elapsed_time = time.time() - start_time
        val1, val2 = read_sensors()
        
        if (online == 0 and (val1 >= IR_THRESHOLD or val2 >= IR_THRESHOLD)) or elapsed_time > 9: # STOP            
            speed = 0
            drive_basic(speed, speed)
            break
        
        if online == 1:
            if val1 < IR_THRESHOLD and val2 < IR_THRESHOLD:
                online = 0
                
        elif MIN_SPEED < speed:
            speed = round(0.95*speed)            
            
    enc1, enc2 = read_encoders(ADDRESS, ENCODERONE)
    return enc1, enc2

def turn_in_place(direction, conn): # for testing purposes, direction == 1 for clockwise, -1 for counterclockwise
    # initialize list of line distances
    line_distances1 = []
    line_distances2 = []
    
    # read sensors to verify we are on a line
    val1, val2 = read_sensors()

    if val1 < IR_THRESHOLD and val2 < IR_THRESHOLD:
        # robot is not on the line!
        print("off line")
        conn.sendall('robot is not on the line!')
        online = False
        return [0], [0]
    
    conn.sendall('robot is on the line,')
    online = True

    # reset encoders
    reset_encoders()
    enc1_a, enc2_a = read_encoders(ADDRESS, ENCODERONE)

    # set initial speed
    # speed = round(TOP_SPEED/5)
    speed = 5
    # initialize line counter
    lines_turned = 0

    # get start time
    start_time = time.time()
    start_flag = False

    # main loop
    while True:
        
        if not start_flag:
            start_flag = True
            
            if direction == 1:
                drive_basic(speed, -speed)
            
            elif direction == -1:
                drive_basic(-speed, speed)          
            
        elapsed_time = time.time() - start_time
        # conn.sendall(str(elapsed_time))
        if elapsed_time > 10:
            conn.sendall('timed out,')
            drive_basic(0, 0)
            return [-1], [-1]                  

        val1, val2 = read_sensors()

        if val1 < IR_THRESHOLD and val2 < IR_THRESHOLD:
            # robot is not on the line!
            if online:
                conn.sendall('gone off line,')
            
            online = False

        elif val1 > IR_THRESHOLD or val2 > IR_THRESHOLD:       
            if not online:
                online = True
                lines_turned += 1
                conn.sendall('lines turned : ' + str(lines_turned) + ',')
                
                enc1_b, enc2_b = read_encoders(ADDRESS, ENCODERONE)
                
                if direction == 1:
                    encoder_distance1 = enc1_b - enc1_a
                    encoder_distance2 = 2**32 - enc2_b
                    
                else:
                    encoder_distance1 = 2**32 - enc1_b
                    encoder_distance2 = enc2_b - enc2_a
                        
                
                # max_distance = max(encoder_distance1, encoder_distance2)
                line_distances1.append(encoder_distance1)
                line_distances2.append(encoder_distance2)

                reset_encoders()
                enc1_a, enc2_a = read_encoders(ADDRESS, ENCODERONE)

                if lines_turned == 2:
                    conn.sendall('breaking')
                    drive_basic(0, 0)
                    break
                
    return line_distances1, line_distances2
            
def turn_lines(n_lines):
    # reset encoders
    reset_encoders()

    # set turning direction
    if n_lines <= 3:
        direction = 1
        
    else:
        n_lines = 6-n_lines
        direction = -1    
           
    # initialize line counter
    lines_turned = 0

    # get initial IR values. Note that we are not yet set up for situation where somehow the robot is not on a line.
    val1, val2 = read_sensors(adc1, adc2)
    
    if val1 < IR_THRESHOLD and val2 < IR_THRESHOLD:
        # robot is lost. Not sure the solution in this case, maybe turn slightly in each direction until line is found?
        onLine = 0
        return 1
    else:
        onLine = 1

    # calculate how far to turn (this is an approximation that allows the robot to aniticipate when it is almost at the target so that it can decelerate)
    dist2turn = DIST_TURN * n_lines

    # set initial speed
    speed = TOP_SPEED

    # turning - main loop
    while lines_turned < n_lines:        
        # read encoders and calculate distance turned
        enc1, enc2 = read_encoders(ADDRESS, ENCODERONE)        
        if direction == 1:
            dist_turned = enc1 
        else:
            dist_turned = enc2 

        # calculate distance left to turn, and reduce speed if getting close to target
        distance_left = dist2turn - dist_turned
        if distance_left < SLOWING_DIST:
            if speed > MIN_SPEED:
                speed = round(speed * .95)

        # read from IR sensors and update lines_turned if on a new line
        val1, val2 = read_sensors(adc1, adc2)

        if val1 > IR_THRESHOLD or val2 > IR_THRESHOLD:
            if online == 0:
                online = 1
                lines_turned += 1
        else:
            if online == 1:
                online = 0

        # set speed or stop the robot if it's reached the number of lines
        if lines_turned == n_lines:
            set_speed(0, SPEED1, 0, SPEED2, writeBuffer, ADDRESS)
        else:
            if direction == 1:
                set_speed(speed, SPEED1, -speed, SPEED2, writeBuffer, ADDRESS)
            else:
                set_speed(-speed, SPEED1, speed, SPEED2, writeBuffer, ADDRESS)
    
    return enc1, enc2

def linear_drive(n_lines):
    # reset encoders
    reset_encoders()

    # initialize line counter
    lines_traversed = 0

    # get initial IR values. Note that we are not yet set up for situation where somehow the robot is not on a line.
    val1, val2 = read_sensors(adc1, adc2)
    
    if val1 < IR_THRESHOLD and val2 < IR_THRESHOLD:
        # robot is lost. Not sure the solution in this case, maybe turn slightly in each direction until line is found?
        online = 0
        return 1
    else:
        online = 1
   
    # set initial speed
    speed = TOP_SPEED

    # driving - main loop
    while lines_traversed < n_lines:        
        # read encoders and calculate distance driven
        enc1, enc2 = read_encoders(ADDRESS, ENCODERONE)        
        dist_driven = (enc1 + enc2)/2

        # read from IR sensors and update lines_turned if on a new line
        val1, val2 = read_sensors(adc1, adc2)

        if val1 > IR_THRESHOLD or val2 > IR_THRESHOLD:
            if online == 0:
                online = 1
                lines_traversed += 1
                reset_encoders()
        else:
            if online == 1:
                online = 0

        # decelerate if nearing the end 
        if (n_lines - lines_traversed == 1) and online == 0:
            if speed > MIN_SPEED:
                speed = speed * .95 

        # straighten out if robot veering off line
        if lines_traversed < n_lines:
            if online == 1 and val1 < IR_THRESHOLD:
                set_speed(speed, SPEED1, speed*0.95, SPEED2, writeBuffer, ADDRESS)
            
            elif online == 1 and val2 < IR_THRESHOLD:
                set_speed(speed*0.95, SPEED1, speed, SPEED2, writeBuffer, ADDRESS)

            else:
                set_speed(speed, SPEED1, speed, SPEED2, writeBuffer, ADDRESS)
            
        else:
            set_speed(0, SPEED1, 0, SPEED2, writeBuffer, ADDRESS)

def honeycomb(list_input):
    # this is the main program for driving the robot
    # list_input is a list of integers; each odd entry refers to number of lines to turn 
    # that step, and each even entry refers to number of lines to drive straight

    for i in range(len(list_input)):
        if i % 2 == 0:
            # turn
            enc1, enc2 = turn_lines(list_input[i])


