with open('/home/pi/Desktop/flowerpotdata.csv','a',encoding='UTF8', newline='') as file:
    writer=csv.writer(file)
    flowerdata = [datetime.now(),Light, SoilMoisture, waterLevel, temp, hum]
    writer.writerow(flowerdata)