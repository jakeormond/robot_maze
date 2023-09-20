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


def turn_in_place_V1(n_lines, conn): # direction == 1 for clockwise, -1 for counterclockwise
    miss_flag = False
    
    conn.sendall('TURN_IN_PLACE,')
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
    speed = INITIAL_TURN_SPEED
    
    # initialize line counter
    lines_turned = 0

    # get start time
    start_time = time.time()   

    # main loop
    counter = 0
    while True:
        counter += 1
        
        encoder_distance1, encoder_distance2 = calculate_distance_turn(enc1_a, enc2_a, direction)
        
        if (min(encoder_distance1, encoder_distance2) > MAX_TURN_DIST) and not (online):
            conn.sendall('encoder dist over limit - ' + str(encoder_distance1) + ' ' + str(encoder_distance2) + ',')
            conn.sendall('sensor vals - ' + str(val1) + ' ' + str(val2) + ',')
            
        if (encoder_distance1 < 0) or (encoder_distance2 < 0):
            conn.sendall('encoders negative,')
        
        if counter%10 == 0:  
            # conn.sendall('TURN_IN_PLACE - LOOP' + str(counter) + ',')
            conn.sendall('enc distance1 = ' + str(encoder_distance1) + ' enc distance2 = ' + str(encoder_distance2) + ',')
        
        # drive and sleep
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
            # conn.sendall('min enc distance = ' + str(min(encoder_distance1, encoder_distance2)) + ',')
            drive_basic(0, 0)
            return [-1], [-1]                  
           
        # accelerate or decelerate depending on how far robot's turned
        #if (lines_turned < (n_lines-1)) or (min(encoder_distance1, encoder_distance2) < 50):  
        #    if speed < MAX_TURN_SPEED:  # accelerate
        #        speed += .3
        #        
        #elif (speed > MIN_SPEED) or miss_flag:  # decelerate
        #    speed -= .3
            
        
        # read sensors 
        val1, val2 = read_sensors()
        conn.sendall('val1 ' + str(val1) + ' val2 ' + str(val2) + ',') 
        # change online flag to False if was True and no longer on line
        if val1 < IR_THRESHOLD and val2 < IR_THRESHOLD:
            if online:
                conn.sendall('gone off line,')            
                online = False
            
            # if missed line, increment lines turned
            elif min(encoder_distance1, encoder_distance2) > MAX_TURN_DIST:
                miss_flag = True
                online = True
                lines_turned += 1
                conn.sendall('enc distance = ' + str(min(encoder_distance1, encoder_distance2)) + ' -  missed line incremented - lines turned : ' + str(lines_turned) + ',')   
                
                line_distances1.append(encoder_distance1)
                line_distances2.append(encoder_distance2)

                enc1_a, enc2_a = reset_encoders()
                conn.sendall('reset encoders,')             
                # conn.sendall('breaking,')
                # drive_basic(0, 0)          
                
                if lines_turned == n_lines: # we have missed the final line, so undoubtedly have turned too far
                    # need to find the line: 1) drive forwards a bit, then 2) turn in opposite
                    # direction until it is found.
                    
                    # drive_basic(0, 0)
                    # conn.sendall('drive forward by distance,')
                    # drive_forward_by_distance(40, conn)
                    # conn.sendall('find line,')
                    # found_flag = find_line(-direction, conn)
                    conn.sendall('missed final line,')
                    break

        # if moved on to line, increment lines_turned
        elif val1 > IR_THRESHOLD and val2 > IR_THRESHOLD:       
            if not online:
                miss_flag = False
                online = True
                lines_turned += 1
                conn.sendall('lines turned : ' + str(lines_turned) + ',')   
                
                line_distances1.append(encoder_distance1)
                line_distances2.append(encoder_distance2)

                enc1_a, enc2_a = reset_encoders()
                conn.sendall('reset enc1_a and enc2a ' + str(enc1_a) + ' ' + str(enc2_a) + ',')

        
                
        if lines_turned == n_lines:
            conn.sendall('speed : ' + str(speed) + ',')
            
            conn.sendall('breaking,')
            drive_basic(0, 0)
            break
                
    return line_distances1, line_distances2


def find_line(direction, conn):
    conn.sendall('FIND LINE,')
    reset_encoders()
    enc1_a, enc2_a = read_encoders(ADDRESS, ENCODERONE)
    
    speed = MIN_SPEED
    
    counter = 0
    while True:
        counter += 1
        
        if counter%10 == 0:  
            conn.sendall('FIND LINE LOOP ' + str(counter) + ',')
        # turn
        if direction == 1:
            drive_basic(speed, -speed)
        else:
            drive_basic(-speed, speed)
        
        print(f'speed = {speed}')
        utime.sleep_ms(10)
        
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