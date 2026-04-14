import requests
import json

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