from machine import Pin
from machine import SoftI2C
import time
from ssd1306 import SSD1306_I2C

i2c0 = SoftI2C(scl=Pin(9),sda=Pin(8), freq=400000)
# Setting up i2c interface to display windows state
display = SSD1306_I2C(128,64,i2c0,addr=0x3c)

# Define motor pins
IN1 = Pin(13, Pin.OUT)
IN2 = Pin(12, Pin.OUT)
IN3 = Pin(11, Pin.OUT)
IN4 = Pin(10, Pin.OUT)
RAIN_SENSOR_PIN = Pin(5,Pin.IN,Pin.PULL_UP)
LIMIT_SWITCH_PIN = Pin(6,Pin.IN,Pin.PULL_UP)

# Half-step sequences (8 steps per cycle - smoother)
STEP_SEQUENCE_CW_HALF = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1]
]

STEP_SEQUENCE_CCW_HALF = [
    [1, 0, 0, 1],  # Reverse order for CCW
    [0, 0, 0, 1],
    [0, 0, 1, 1],
    [0, 0, 1, 0],
    [0, 1, 1, 0],
    [0, 1, 0, 0],
    [1, 1, 0, 0],
    [1, 0, 0, 0]
]

def is_Window_Open():
    if LIMIT_SWITCH_PIN.value()==1:
        return True #print("Window Open")
    else:
        return False #print("Window Closed")

def is_It_Raining():
    if RAIN_SENSOR_PIN.value()==1:
        return False
    else:
        return True

def rotate_ccw(steps, delay_ms=1):
    """Rotate the motor clockwise using half-step mode."""
    sequence = STEP_SEQUENCE_CW_HALF
    step_count = len(sequence)
    for _ in range(abs(steps)):
        for step in range(step_count):
            IN1.value(sequence[step][0])
            IN2.value(sequence[step][1])
            IN3.value(sequence[step][2])
            IN4.value(sequence[step][3])
            time.sleep_ms(delay_ms)

def rotate_cw(steps, delay_ms=1):
    """Rotate the motor counterclockwise using half-step mode."""
    sequence = STEP_SEQUENCE_CCW_HALF
    step_count = len(sequence)
    for _ in range(abs(steps)):
        for step in range(step_count):
            IN1.value(sequence[step][0])
            IN2.value(sequence[step][1])
            IN3.value(sequence[step][2])
            IN4.value(sequence[step][3])
            time.sleep_ms(delay_ms)
while True:
    if is_Window_Open() and is_It_Raining():
        display.text("Raining-",0,6)
        display.text("Closing window",0,16)
        display.show()
        rotate_cw(272)
    elif not is_Window_Open() and is_It_Raining():
        display.text("Raining-",0,6)
        display.text("Window is closed",0,16)
        display.show()
        
    elif is_Window_Open() and not is_It_Raining():
        display.text("Dry Weather-",0,6)
        display.text("Window is open",0,16)
        display.show()
    elif not is_Window_Open() and not is_It_Raining():
        display.text("Dry Weather-",0,6)
        display.text("Opening window",0,16)
        display.show()
        rotate_ccw(272)
    display.fill(0)
    time.sleep(1)
    

