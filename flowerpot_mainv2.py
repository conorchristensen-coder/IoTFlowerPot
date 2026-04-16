from time import sleep, strftime
import requests
from datetime import datetime
import paho.mqtt.client as MyMqtt
import json, random
import RPi.GPIO as GPIO
import csv
from StepperMotor_MODULE import StepperMotor

# motor, read_Light(), read_SoilMoisture(), read_LeftLim(), read_RightLim(), pump_ON(), pump_OFF()
from Flowerpot_Engine import*

# -----------------------------
# Configuration
# -----------------------------
# 
# DATA_FILE = "light_log.csv"
# 
# MOISTURE_THRESHOLD = 30  # Soil moisture threshold %
# NOAA_API_URL = "https://api.weather.gov/gridpoints/SEW/124,67/forecast"  # Replace with your local gridpoint
# 
# -----------------------------
# Initialize CSV file
# -----------------------------
# try:
#     with open(DATA_FILE, 'x', newline='') as f:
#         writer = csv.writer(f)
#         writer.writerow(["Timestamp", "MaxLightPercent"])
# except FileExistsError:
#     pass  # File already exists



# -----------------------------
# Moisture and NOAA watering function
# -----------------------------
def check_weather_and_water():
    """Check NOAA forecast and soil moisture, water if dry and no rain predicted."""
    try:
        # Get NOAA forecast
        response = requests.get(NOAA_API_URL, timeout=10)
        response.raise_for_status()
        forecast_data = response.json()

        # Determine if rain is predicted today
        periods = forecast_data['properties']['periods']
        rain_predicted = any('rain' in p['detailedForecast'].lower() for p in periods)

        # Read current soil moisture
        soil_moisture = read_SoilMoisture()
        print(f"Soil moisture: {soil_moisture}% | Rain predicted: {rain_predicted}")

        # Watering decision using Flowerpot_Engine pump functions
        if rain_predicted:
            print("Rain predicted today. Skipping watering.")
            pump_OFF()
        elif soil_moisture < MOISTURE_THRESHOLD:
            print("Soil is dry and no rain predicted. Watering plant...")
            pump_ON()
            sleep(30)  # Water duration (adjust as needed)
            pump_OFF()
        else:
            print("Soil moisture sufficient. No watering needed.")

    except Exception as e:
        print(f"Error checking weather or watering: {e}")


# -----------------------------
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
    
def publishJSON(data_out):
    
    # Convert data into JSON to send to MQTT server
    # First format data as a dictionary
    

    print("data_out=",data_out)
    JSON_data_out = json.dumps(data_out)    # Convert to JSON format
    client.publish(TelemetryTopic, JSON_data_out, 0)
    time.sleep(2)
    print('---------------------------')

def on_message(client, userdata, msg):
    global clickedMOVE
    if msg.topic.startswith('v1/devices/me/rpc/request/'):
        clickedMOVE = True
        
def getValue(params):

    client.publish(AttributesTopic, json.dumps(pump), 1) 
    client.publish(AttributesTopic, json.dumps(Led), 1)
    client.publish(AttributesTopic, json.dumps(waterLevel),1)
    
def setValue(params):
    
    client.publish(AttributesTopic, json.dumps(pump), 1) 
    client.publish(AttributesTopic, json.dumps(Led), 1)
    client.publish(AttributesTopic, json.dumps(waterLevel),1)
    

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
        
        daytemp = fetchweatherdata()[0]
        sun = fetchweatherdata()[1]
        if read_WaterLevel() == 'full' and read_SoilMoisture() <= 10:
            print(read_SoilMoisture())

            if daytemp >= 65:
                if sun == 'Sunny' or sun == 'Mostly Sunny' or sun == 'Partly Sunny' or sun == 'Partly Clear' or sun == 'Mostly Clear' or sun == 'Clear':
                    pump_ON()
                    sleep(15)
                    pump_OFF() 
            else:
                pump_ON()
                sleep(10)
                pump_OFF()
        elif read_WaterLevel() == 'empty':
            print('NEEDS WATER')
            Led["LedRunning"] = True
        else:
            print("Sall Good")
            Led["LedRunning"] = False
        
        i=i+1
        now = datetime.now()

        # Daily watering at 8 AM
        if now.hour == 8 and (last_watered_date != now.date()):
            check_weather_and_water()
            last_watered_date = now.date()

        # Light optimization sweep
        
        sweep_and_optimize_light(5,0.5)
        print(f"Waiting {1200/60:.0f} minutes until next light optimization...")
        sleep(20*60)
        
        i=i+1
        
        home_base()

except KeyboardInterrupt:
    print("Exiting program...")
    GPIO.cleanup()
    client.disconnect()
    client.loop_stop()