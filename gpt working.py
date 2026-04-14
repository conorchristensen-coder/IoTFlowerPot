from time import sleep
import paho.mqtt.client as MyMqtt
import json, random
import RPi.GPIO as GPIO
from StepperMotor_MODULE import StepperMotor
from Flowerpot_Engine import *

# -----------------------------
# Initialize motor and variables
# -----------------------------
motor = StepperMotor()

LIGHT_SENSOR_PIN = 8      # Placeholder for your light sensor
TARGET_LIGHT = 500        # Minimum light level we want

# Simple function to read light
def read_light():
    """
    Returns current light level.
    Replace the return value with actual sensor read.
    """
    # For testing, return a random light value
    return random.randint(100, 600)

# Simple feedback loop for light
def adjust_light_motor(target_light, max_attempts=50):
    attempts = 0
    current_light = read_light()
    
    while current_light < target_light and attempts < max_attempts:
        print("Current light:", current_light, "- rotating motor to find more light")
        motor.rotate(1, 'CCW', 's', 'full')  # rotate motor
        sleep(0.2)  # small delay for sensor to stabilize
        current_light = read_light()
        attempts += 1

    if current_light >= target_light:
        print("Target light reached:", current_light)
    else:
        print("Max attempts reached. Current light:", current_light)

# -----------------------------
# MQTT setup
# -----------------------------
iot_hub = "thingsboard.cloud"
port = 1883
cli_ID = f'clientID-{random.randint(0, 1000)}'
username = "1k06jk6MY3O3tpx1BE7Y"  # ADD YOUR CODE HERE
password = ""
RPCrequestTopic = 'v1/devices/me/rpc/request/+'
AttributesTopic = "v1/devices/me/attributes"

pump = {"PumpRunning": False}
Led = {"LedRunning": False}

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connection: {rc}")
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
        # Adjust motor to reach target light
        adjust_light_motor(TARGET_LIGHT)
        sleep(5)  # Wait 5 seconds before checking again

except KeyboardInterrupt:
    GPIO.cleanup()
    client.disconnect()
    client.loop_stop()
    
    