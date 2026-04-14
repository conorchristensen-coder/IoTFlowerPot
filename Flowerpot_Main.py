## Mech 405
## Term Project

from time import sleep
import paho.mqtt.client as MyMqtt
import json, random
import RPi.GPIO as GPIO
from StepperMotor_MODULE import StepperMotor
from Flowerpot_Engine import*

# Define motor
motor = StepperMotor()

# Initialize variables and MQTT details
iot_hub = "thingsboard.cloud"
port = 1883
cli_ID = f'clientID-{random.randint(0, 1000)}'
username = "1k06jk6MY3O3tpx1BE7Y"    # <---------------------------------- ADD YOUR CODE HERE
password = ""
RPCrequestTopic = 'v1/devices/me/rpc/request/+'
AttributesTopic = "v1/devices/me/attributes"

pump = {"PumpRunning": False}
Led = {"LedRunning" : False}
waterLevel = {"empty": True}


# MQTT on_connect callback function
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connection: {rc}")
    client.subscribe(RPCrequestTopic)
    
    client.publish(AttributesTopic, json.dumps(pump), 1) 
    client.publish(AttributesTopic, json.dumps(Led), 1)
    client.publish(AttributesTopic, json.dumps(waterLevel),1)


# MQTT on_message callback function
def on_message(client, userdata, msg):
    # Make globally available for all parts of the program to use 
    global clickedMOVE ## From exam but works for any RPC functions
    if msg.topic.startswith('v1/devices/me/rpc/request/'):
        # remote TB button was clicked
        clickedMOVE = True ## All of this could be altered for specific cases



# Set up MQTT
client = MyMqtt.Client(client_id=cli_ID, callback_api_version=MyMqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(username, password)
client.connect(iot_hub, port)
client.loop_start()



try:
    while True:
    # Do Stuff, main body of program
        i = 1

except:
  # keyboard interrupt
    GPIO.cleanup()
    client.disconnect()
    client.loop_stop()