import RPi.GPIO as GPIO
from StepperMotor_MODULE import StepperMotor
from time import sleep,strftime
import time, AHT20
from ADC_PCF8591 import PCF8591
import csv
import requests



# This module contains all initializations and functions
# for the smart Flowerpot

# Devices (pins are for the LAB prototype)
WaterLevelPin = 12    # Pin number on the header (GPIO 18)
PumpPin = 36    # Pin number on the header (GPIO 16)
LedPin = 8    # Pin number on the header (UART0 TX)
ButtonPin = 16   # Pin number on the header (GPIO 23)
LeftLim = 7    # Pin number on the header (GPIO 4)
RightLim = 18   # Pin number on the header (GPIO 24)

# Define LED state variable
ledON = False

# Define motor
motor = StepperMotor()
motor.printOutput = False

# I2C bus connections for ADC and AHT20
bus = 1

# set up the ADC device
ADC_address = 0x48   # ADC board
A0_chan = 0x40       # A0 input    (Light sensor)
A1_chan = 0x41       # A1 input    (Soil misture sensor)
A2_chan = 0x42       # A2 input
A3_chan = 0x43       # A3 input
ADC = PCF8591(bus, ADC_address)

# set up AHT20 device for temperature andi humidity
AHT20_address = 0x38   # AHT20 sensor board
aht20 = AHT20.AHT20(bus, AHT20_address)

# Initialize GPIO
GPIO.setmode(GPIO.BOARD)    # Number GPIOs by its physical location
GPIO.setwarnings(False)     # Turn of GPIO warnings

# Initialize water level sensor
GPIO.setup(WaterLevelPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)   # Set pin mode as input
# Initialize pump relay
GPIO.setup(PumpPin, GPIO.OUT, initial=GPIO.LOW)   # Set pin mode as output and turn off pump
# Initialize LED
GPIO.setup(LedPin, GPIO.OUT, initial=GPIO.LOW)   # Set pin mode as output and turn off LED
# Initialize Button
GPIO.setup(ButtonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)   # Set pin mode as input
# Initialize Left limit switch
GPIO.setup(LeftLim, GPIO.IN, pull_up_down=GPIO.PUD_UP)   # Set pin mode as input
# Initialize Right limit switch
GPIO.setup(RightLim, GPIO.IN, pull_up_down=GPIO.PUD_UP)   # Set pin mode as input

global DATA_FILE
global MOISTURE_THRESHOLD
global NOAA_API_URL

DATA_FILE = "light_log.csv"
MOISTURE_THRESHOLD = 30  # Soil moisture threshold %
NOAA_API_URL = "https://api.weather.gov/gridpoints/SEW/124,67/forecast"  # Replace with your local gridpoint


try:
    with open(DATA_FILE, 'x', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "MaxLightPercent"])
except FileExistsError:
    pass  # File already exists

# Weather station at the PDX Airport
latitude = '45.5958'
longitude = '-122.6093'
office = 'PQR'
gridX = '115'
gridY = '106'

# URL and query elements for the NOAA Web site
base_url = 'https://api.weather.gov/gridpoints/'
full_url = base_url + office + '/' + gridX + ',' + gridY + '/forecast'


def fetchweatherdata(): 
    # GET the response from the NWS server
    response = requests.get(full_url)

    # Format the response object as JSON
    data = response.json()
    global daytemp, sun
    daytemp = data['properties']['periods'][0]['temperature']
    sun = data['properties']['periods'][0]['shortForecast']
    return (daytemp,sun)



def button_callback(ButtonPin):
    # Read button
    global ledON
    if GPIO.input(ButtonPin) == False and not ledON:
        # Button was pressed and LED was off
        # Turn LED ON
        print("  turn led ON .............")
        ledON = led_ON()
        time.sleep(1)
    elif GPIO.input(ButtonPin) == False and ledON:
        # Button was pressed and LED was already on
        # Turn LED off
        print("    turn led OFF .............")
        ledON = led_OFF()
        time.sleep(1)
                

# Set up event detection on the ButtonPin.  Signal goes low when button is pressed
GPIO.add_event_detect(ButtonPin, GPIO.FALLING, callback=button_callback, bouncetime=100)


def read_Light():
    # Read light sensor (CH0 of the A/D)
    raw_value = ADC.read(A0_chan)
    # Convert into percentage
    percentLight = round((raw_value/255)*100, 2)
    return percentLight


def read_WaterLevel():
    # Read water level sensor (T/F)
    if GPIO.input(WaterLevelPin):
        return "full"
    elif not GPIO.input(WaterLevelPin):
        return "empty"
     
     
def read_SoilMoisture():
    # Read soil moisture sensor (CH1 of the A/D)
    raw_value = ADC.read(A1_chan)
    # Convert into percentage
    percentSoilMoisture = round((raw_value/255)*100, 2)
    return percentSoilMoisture


def read_TempHum():
    # Read the temprature and humidity from the AHT20 sensor
    temperature = aht20.get_temperature()
    humidity = aht20.get_humidity()
    return temperature, humidity


def pump_ON():
    # Turn the pump on
    GPIO.output(PumpPin, GPIO.HIGH)
    return True


def pump_OFF():
    # Turn the pump off
    GPIO.output(PumpPin, GPIO.LOW)
    return False


def led_ON():
    # Turn the LED on
    GPIO.output(LedPin, GPIO.HIGH)
    return True


def led_OFF():
    # Turn the LED off
    GPIO.output(LedPin, GPIO.LOW)
    return False


def read_LeftLim():
    # Read Left limit switch (T/F)
    if GPIO.input(LeftLim):
        return True
    elif not GPIO.input(LeftLim):
        return False


def read_RightLim():
    # Read Right limit switch (T/F)
    if GPIO.input(RightLim):
        return True
    elif not GPIO.input(RightLim):
        return False


def home_base():
    # Rotate the base until the right limit switch is clicked.
    # Then, rotate back 90 deg to the center of the range
    while(not read_RightLim()):
        # rotate the base until the right limit switch is triggered
        motor.rotate(1, 'CCW', 's', 'full')
    
    print("Right limit SW hit")
    # Move back to center of the range
    print("Moving back to center of the range")
    time.sleep(1)
    motor.rotate(90, 'CW', 's', 'full')
    return True
            
    
def sweep_and_optimize_light(step_deg, sweep_delay):
    
    
    STEP_DEG = 5
    SWEEP_DELAY = 0.5
    SWEEP_INTERVAL = 20*60
    MAX_DEGREES = 90   
    
      # Motor physical limits
    """Sweep motor across full ±90° range, find highest light, move back, log it."""
    # Move to leftmost limit
    motor_pos = 0
    while motor_pos > -MAX_DEGREES and not read_LeftLim():
        motor.rotate(step_deg, 'CCW', 's', 'full')
        motor_pos -= step_deg
        sleep(0.05)

    # Sweep right while recording light
    sweep_positions = []
    sweep_lights = []
    current_pos = motor_pos
    while current_pos < MAX_DEGREES and not read_RightLim():
        light = read_Light()
        sweep_positions.append(current_pos)
        sweep_lights.append(light)
        motor.rotate(step_deg, 'CW', 's', 'full')
        current_pos += step_deg
        sleep(sweep_delay)

    # Find max light position
    max_index = sweep_lights.index(max(sweep_lights))
    best_pos = sweep_positions[max_index]
    max_light = sweep_lights[max_index]
    print(f"Max light {max_light}% at {best_pos}°")

    # Move motor to best position
    steps_to_move = best_pos - current_pos
    if steps_to_move != 0:
        direction = 'CW' if steps_to_move > 0 else 'CCW'
        motor.rotate(abs(steps_to_move), direction, 's', 'full')
        motor_pos = best_pos
    print(f"Motor moved to optimal light position: {motor_pos}°")

    # Log data to CSV
    timestamp = strftime("%Y-%m-%d %H:%M:%S")
    with open(DATA_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, max_light])
    print(f"Logged data: {timestamp}, {max_light}%")
    return max_light, timestamp
