from time import sleep
import paho.mqtt.client as MyMqtt
import json, random
import RPi.GPIO as GPIO
from StepperMotor_MODULE import StepperMotor
from Flowerpot_Engine import *  # Provides motor, read_Light(), read_SoilMoisture(), read_TempHum(), etc.

# -----------------------------
# Configuration
# -----------------------------
TARGET_LIGHT = 50   # Light threshold in percent (matches read_Light output)
CHECK_INTERVAL = 5  # Seconds between each light check
MAX_ATTEMPTS = 50   # Safety limit for motor rotation attempts

rotation = {"RotatingLeft" :False, "RotatingRight" : False}


# -----------------------------
# Light feedback function
# -----------------------------
def adjust_light_motor(target_light, max_attempts=MAX_ATTEMPTS):
    attempts = 0
    current_light = read_Light()
    
    while current_light < target_light and attempts < max_attempts:
        print(f"Current light: {current_light}%. Rotating motor to find more light...")
        if read_LeftLim() == False and rotation["RotatingLeft"] == False:
            rotation["RotatingLeft"] = True
            motor.rotate(5, 'CCW', 's', 'full')  # rotate a few steps clockwise
            sleep(0.2)  # allow sensor to stabilize
            current_light = read_Light()
            attempts += 1
        elif read_LeftLim() == True:
            rotation["RotatingRight"] = True
            motor.rotate(5, 'CW', 's', 'full')  # rotate a few steps clockwise
            sleep(0.2)  # allow sensor to stabilize
            current_light = read_Light()
            attempts += 1
            
    if current_light >= target_light:
        print(f"Target light reached: {current_light}%")
    else:
        print(f"Max attempts reached. Current light: {current_light}%")

# -----------------------------
# MQTT setup
# -----------------------------
iot_hub = "thingsboard.cloud"
port = 1883
cli_ID = f'clientID-{random.randint(0,1000)}'
username = "1k06jk6MY3O3tpx1BE7Y"  # Add your key
password = ""
RPCrequestTopic = 'v1/devices/me/rpc/request/+'
AttributesTopic = "v1/devices/me/attributes"

pump = {"PumpRunning": False}
Led = {"LedRunning": False}

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"MQTT Connection: {rc}")
    client.subscribe(RPCrequestTopic)

def on_message(client, userdata, msg):
    global clickedMOVE
    if msg.topic.startswith('v1/devices/me/rpc/request/'):
        clickedMOVE = True

client = MyMqtt.Client(client_id=cli_ID, callback_api_version=MyMqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(username, password)
client.connect(iot_hub, port)
client.loop_start()

# -----------------------------
# Main loop
# -----------------------------
try:
    while True:
        # Rotate motor to optimize light
        adjust_light_motor(TARGET_LIGHT)
        sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    print("Exiting program...")
    GPIO.cleanup()
    client.disconnect()
    client.loop_stop()