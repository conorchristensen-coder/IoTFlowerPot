from time import sleep, strftime
import requests
from datetime import datetime
import paho.mqtt.client as MyMqtt
import json, random
import RPi.GPIO as GPIO
import csv
from StepperMotor_MODULE import StepperMotor
from Flowerpot_Engine import*

# MQTT setup
# -----------------------------
iot_hub = "thingsboard.cloud"
port = 1883
cli_ID = f'clientID-{random.randint(0,1000)}'
username = "1k06jk6MY3O3tpx1BE7Y"  # Replace with your key
password = ""
TelemetryTopic = "v1/devices/me/telemetry"
RPCrequestTopic = 'v1/devices/me/rpc/request/+'
AttributesTopic = "v1/devices/me/attributes"


pump = {"PumpRunning": False}
Led = {"LedRunning": False}


def on_connect(client, userdata, flags, rc, properties=None):
    print(f"MQTT Connection: {rc}")
    client.subscribe(RPCrequestTopic)
    client.publish(AttributesTopic, json.dumps(pump), 1) 
    client.publish(AttributesTopic, json.dumps(Led), 1) 
def publishJSON(data_out):
    
    # Convert data into JSON to send to MQTT server
    # First format data as a dictionary
    

    print("data_out=",data_out)
    JSON_data_out = json.dumps(data_out)    # Convert to JSON format
    client.publish(TelemetryTopic, JSON_data_out, 0)
    time.sleep(2)
    print('---------------------------')

def on_message(client, userdata, msg):
    if msg.topic.startswith('v1/devices/me/rpc/request/'):
        data = json.loads(msg.payload)
        if data['method'] == 'setValue':
            params = data['params']
            # Turn the pump on/off
            setValue(params)


def on_message(client, userdata, msg):
    if msg.topic.startswith('v1/devices/me/rpc/request/'):
        data = json.loads(msg.payload)
        if data['method'] == 'setValue':
            params = data['params']
            # Turn the pump on/off
            setValue(params)
       
def getValue(params):

    client.publish(AttributesTopic, json.dumps(pump), 1) 
    client.publish(AttributesTopic, json.dumps(waterLevel),1)
    client.publish(AttributesTopic, json.dumps(Led),1)
    
def setValue(params):
    if params == True:
        # Turn pump ON
        pump_ON()
        pump['PumpRunning'] = True
        # Update the ClientAttribute "PumpRunning" on the TB dashboard
        client.publish(AttributesTopic, json.dumps(pump), 1)

    elif params == False:
        # Turn pump OFF
        pump_OFF()
        pump['PumpRunning'] = False
        # Update the ClientAttribute "PumpRunning" on the TB dashboard
        client.publish(AttributesTopic, json.dumps(pump), 1)
        

client = MyMqtt.Client(client_id=cli_ID, callback_api_version=MyMqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(username, password)
client.connect(iot_hub, port)
client.loop_start()

# -----------------------------
# Main loop
# -----------------------------
last_watered_date = None

try:
    i = 1
    while True:
        
        percentLight = read_Light()
        publishJSON({"Packet":i,"Light":percentLight})
        
        percentSoilMoisture = read_SoilMoisture()
        publishJSON({"Packet":i,"SoilMoisture":percentSoilMoisture})
        
        tempHum = read_TempHum()
        
        temp = tempHum[0]
        publishJSON({"Packet":i,"Temperature":temp})
        
        
        hum = tempHum[1]
        publishJSON({"Packet":i,"Humidity":hum})
        
        if read_WaterLevel() == 'full' and read_SoilMoisture() <= 15:
            print(read_SoilMoisture())

            if daytemp >= 65:
                if sun == 'Sunny' or sun == 'Mostly Sunny' or sun == 'Partly Sunny' or sun == 'Partly Clear' or sun == 'Mostly Clear' or sun == 'Clear':
                    pump_ON()
                    sleep(10)
                    pump_OFF() 
            else:
                pump_ON()
                sleep(5)
                pump_OFF()
        elif read_WaterLevel() == 'empty':
            print('NEEDS WATER')
            Led["LedRunning"] = True
        else:
            print("WATER OK")
            Led["LedRunning"] = False
        
        now = datetime.now()

        # Daily watering at 8 AM
        if now.hour == 8 and (last_watered_date != now.date()):
            check_weather_and_water()
            last_watered_date = now.date()

        # Light optimization sweep
        home_base()
        sweep_and_optimize_light(5,0.5)
        print(f"Waiting {1800/60:.0f} minutes until next light optimization...")
        sleep(60*30)
        
        i=i+1
        
        

except KeyboardInterrupt:
    print("Exiting program...")
    GPIO.cleanup()
    client.disconnect()
    client.loop_stop()