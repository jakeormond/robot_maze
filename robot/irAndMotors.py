from machine import Pin, ADC, I2C
import time

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

SOFTWAREREG = 0x0D
SPEED1 = 0x00
SPEED2 = 0x01
VOLTREAD = 0x0A
ENCODERONE = 0x02
CMD = 0x10
RESETENCODERS = 0x20
MODE = 0x0F

speed = 127
mode = 1
address = 0x58

writeBuffer=bytearray(2)

# set mode
writeBuffer[0] = MODE
writeBuffer[1] = 1
i2c.writeto(address,writeBuffer)

# function for setting speed
def set_speed(speed1, SPEED1, speed2, SPEED2, writeBuffer, address):
    writeBuffer[0] = SPEED1;
    writeBuffer[1] = speed1;
    i2c.writeto(address,writeBuffer)

    writeBuffer[0] = SPEED2;
    writeBuffer[1] = speed2;
    i2c.writeto(address,writeBuffer)

# function for reading encoders
def read_encoders(address, ENCODERONE):
    readBuffer = i2c.readfrom_mem(address, ENCODERONE, 8)
    enc1 = (readBuffer[0]<<24) + (readBuffer[1]<<16) + (readBuffer[2]<<8) + readBuffer[3]
    enc2 = (readBuffer[4]<<24) + (readBuffer[5]<<16) + (readBuffer[6]<<8) + readBuffer[7]
    return enc1, enc2

def drive():  
    # reset encoders  
    writeBuffer[0] = CMD
    writeBuffer[1] = RESETENCODERS
    i2c.writeto(address,writeBuffer)
    enc1, enc2 = read_encoders(address, ENCODERONE)
    print(enc1,enc2)

    # loop reading IR sensors and controlling motors based on sensor readings
    i = 1
    while i < 20:
        val1 = adc1.read_u16()
        val2 = adc2.read_u16()
        print(val1, val2)
    
        if val1 < 5000 and val2 < 5000:
            speed = 0

        else:
            speed = 127
    
        print(val1, val2)
    
        set_speed(speed, SPEED1, speed, SPEED2, writeBuffer, address)
        
        time.sleep_ms(100)    

        i += 1


    #writeBuffer=bytearray(1)
    #writeBuffer[0] = VOLTREAD;
    #i2c.writeto(address,writeBuffer)
    #readBuffer = i2c.readfrom(address, 1)

    readBuffer = i2c.readfrom_mem(address, VOLTREAD, 1)
    print(readBuffer[0])


    readBuffer = i2c.readfrom_mem(address, MODE, 1)
    print('mode', readBuffer)

    #writeBuffer=bytearray(1)
    #writeBuffer[0] = ENCODERONE;
    #i2c.writeto(address,writeBuffer)
    time.sleep_ms(1000)

    enc1, enc2 = read_encoders(address, ENCODERONE)
    print(enc1,enc2)




