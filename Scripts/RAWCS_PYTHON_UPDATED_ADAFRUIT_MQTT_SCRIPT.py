from machine import Pin
from machine import SoftI2C
from ssd1306 import SSD1306_I2C
import network, time, usocket, ssl
from umqtt.simple import MQTTClient
import _thread


i2c0 = SoftI2C(scl=Pin(9),sda=Pin(8), freq=400000)
# Setting up i2c interface to display windows state
display = SSD1306_I2C(128,64,i2c0,addr=0x3c)

#---- Wi-Fi ----
WIFI_SSID = "Sk3tchyW1f1"
WIFI_PASSWORD = "H4ck3r'sW1f1"

# ---- Adafruit IO ----
AIO_USERNAME = "RAWCS"
AIO_KEY = "RANDOM_KEY"
AIO_SERVER = "io.adafruit.com"
FEED_STATUS = AIO_USERNAME + "/feeds/window-status-checker"


# ----------------- EXISTING WIFI CODE -----------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    # Display connecting WiFi
    display.fill(0)
    display.text("Connecting", 0, 6)
    display.text("WiFi",0, 16)
    display.show()
    
    # Animated dots for 5 seconds max
    for i in range(5):
        display.text("." * (i+1), 36, 16)
        display.show()
        time.sleep(1)

    # Wait until connected
    while not wlan.isconnected():
        display.text("Waiting for network...", 0, 20)
        display.show()
        time.sleep(8)

    # WiFi connected
    display.fill(0)
    display.text("WiFi Connected", 0, 6)
    display.text(f"IP: {wlan.ifconfig()[0]}", 0, 18)
    display.show()
    time.sleep(3)  # hold message so user can read

    # Internet check
    display.fill(0)
    display.text("Checking",0,6)
    display.text("Internet", 0, 16)
    display.show()
    
    for i in range(5):
        display.text("." * (i+1), 65, 16)
        display.show()
        time.sleep(1)
    try:
        addr = usocket.getaddrinfo("www.google.com", 443)[0][-1]
        s = usocket.socket()
        s.settimeout(5)
        s.connect(addr)
        s = ssl.wrap_socket(s)
        s.write(b"GET / HTTP/1.0\r\nHost: www.google.com\r\n\r\n")
        data = s.read(1024)
        s.close()

        if b"HTTP" in data:
            display.fill(0)
            display.text("Internet Access", 0, 6)
            display.text("Successful", 0, 16)
            display.show()
            time.sleep(6)  # dramatic pause
        else:
            display.fill(0)
            display.text("Internet Issue", 0, 6)
            display.show()
            time.sleep(6)
    except Exception as e:
        display.fill(0)
        display.text("No Internet", 0, 6)
        display.show()
        time.sleep(6)

    # Clear display before main loop
    display.fill(0)
    display.show()

# ----------------- EXISTING HARDWARE SETUP -----------------
IN1 = Pin(13, Pin.OUT)
IN2 = Pin(12, Pin.OUT)
IN3 = Pin(11, Pin.OUT)
IN4 = Pin(10, Pin.OUT)
RAIN_SENSOR_PIN = Pin(5, Pin.IN, Pin.PULL_UP)
LIMIT_SWITCH_PIN = Pin(6, Pin.IN, Pin.PULL_UP)

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
    [1, 0, 0, 1],
    [0, 0, 0, 1],
    [0, 0, 1, 1],
    [0, 0, 1, 0],
    [0, 1, 1, 0],
    [0, 1, 0, 0],
    [1, 1, 0, 0],
    [1, 0, 0, 0]
]

def test_MQTT():
    display.fill(0)
    display.text("Connecting", 0, 6)
    display.text("MQTT",0,16)
    display.show()
    for i in range(5):
        display.text("." * (i+1), 36, 16)
        display.show()
        time.sleep(1)
    
    client = MQTTClient("RA-WCS", AIO_SERVER,
                        user=AIO_USERNAME,
                        password=AIO_KEY)
    client.connect()

    display.fill(0)
    display.text("MQTT Connected", 0, 6)
    display.text("Ready to operate", 0, 16)
    display.show()
    time.sleep(6)  # dramatic pause
    display.fill(0)
    display.show()
    
    return client

# ----------------- MQTT WRAPPER -----------------
def mqtt_connect():
    print("Connecting MQTT")    
    client = MQTTClient("RA-WCS", AIO_SERVER,
                        user=AIO_USERNAME,
                        password=AIO_KEY)
    client.connect()
    print("MQTT Connected")
    print("Ready to operate") 
    return client

# ---------- MQTT PUBLISH HELPER ----------
def mqtt_publish(client, feed, value):
    try:
        client.publish(feed, str(value))
        print(f"📤 Published to {feed}: {value}")
    except Exception as e:
        print("⚠️ MQTT publish failed:", e)



# ----------------- SENSOR + ACTUATOR FUNCTIONS -----------------
def is_Window_Open():
    return LIMIT_SWITCH_PIN.value() == 1

def is_It_Raining():
    return RAIN_SENSOR_PIN.value() == 0

def rotate_ccw(steps, delay_ms=1):
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
    sequence = STEP_SEQUENCE_CCW_HALF
    step_count = len(sequence)
    for _ in range(abs(steps)):
        for step in range(step_count):
            IN1.value(sequence[step][0])
            IN2.value(sequence[step][1])
            IN3.value(sequence[step][2])
            IN4.value(sequence[step][3])
            time.sleep_ms(delay_ms)
            
            
# ---------- MOTOR + SENSOR + DISPLAY THREAD ----------
def motor_sensor_loop():
    while True:
        raining = is_It_Raining()
        window_open = is_Window_Open()

        # Display + motor logic
        if window_open and raining:
            display.text("Raining-",0,6)
            display.text("Closing window",0,16)
            display.show()
            rotate_cw(272)
        elif not window_open and raining:
            display.text("Raining-",0,6)
            display.text("Window is closed",0,16)
            display.show()
        elif window_open and not raining:
            display.text("Dry Weather-",0,6)
            display.text("Window is open",0,16)
            display.show()
        elif not window_open and not raining:
            display.text("Dry Weather-",0,6)
            display.text("Opening window",0,16)
            display.show()
            rotate_ccw(272)

        display.fill(0)
        time.sleep(1)  # refresh/display + sensor check every second

# ---------- MQTT THREAD ----------
def mqtt_loop():
    client = mqtt_connect()
    while True:
        raining = is_It_Raining()
        window_open = is_Window_Open()
        if not window_open and raining:
            mqtt_publish(client, FEED_STATUS, "RAINING- Window is Closed")
        else:
            mqtt_publish(client, FEED_STATUS, "DRY WEATHER- Window is Open")  
        time.sleep(8)  # publish every 5 seconds

# ---------- START THREADS ----------
connect_wifi()
test_MQTT()
_thread.start_new_thread(motor_sensor_loop, ())
_thread.start_new_thread(mqtt_loop, ())

# main thread can stay idle
while True:
    time.sleep(1)
