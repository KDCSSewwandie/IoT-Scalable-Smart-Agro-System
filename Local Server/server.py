from datetime import datetime, time
import requests
import threading
import logging
from time import sleep

import asyncio
import websockets  # type: ignore

import json

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask import render_template

sections = []
dataSet = {}
thresholdWaterLevel = 20
thresholdFertilizerLevel = 20
waterLevel = 40
fertilizerLevel = 60

import asyncio
from datetime import datetime, time
import json

class Section:
    def __init__(self, number, name):
        self.number = number
        self.name = name
        self.humidityThreshold = 45
        self.moistureThreshold = 60
        self.maxWateringLight = 50
        self.latestHumidity = 46
        self.latestTemperature = 28
        self.latestMoisture = 61
        self.latestLight = 51
        self.mode = "Auto"
        self.morning_start = time(6, 0)  # 06:00 AM
        self.morning_end = time(9, 0)    # 09:00 AM
        self.evening_start = time(17, 0)  # 05:00 PM
        self.evening_end = time(19, 0)    # 07:00 PM
        self.water_valve = False
        self.fertilizer_valve = False
        
    def update(self, number, name, humidityThreshold, moistureThreshold, maxWateringLight, mode, morning_start, morning_end, evening_start, evening_end):
        self.number = number
        self.name = name
        self.humidityThreshold = humidityThreshold
        self.moistureThreshold = moistureThreshold
        self.maxWateringLight = maxWateringLight
        self.latestHumidity = 46
        self.latestTemperature = 28
        self.latestMoisture = 61
        self.latestLight = 51
        self.mode = mode
        self.morning_start = self._convert_to_time(morning_start)
        self.morning_end = self._convert_to_time(morning_end)
        self.evening_start = self._convert_to_time(evening_start)
        self.evening_end = self._convert_to_time(evening_end)
        self.water_valve = False
        self.fertilizer_valve = False

    def _convert_to_time(self, time_string):
        if(len(time_string)>6):
            return datetime.strptime(time_string, "%H:%M:%S").time()    
        else:
            return datetime.strptime(time_string, "%H:%M").time()

    async def _sendToClients(self, command):
        if clients:
            try:
                for client in clients:
                    await client.send(command)
            except websockets.exceptions.ConnectionClosed:
                print("Client disconnected")
        else:
            print("No clients connected")
         
    def _openWater(self):
        command = "open valve section " + str(self.number) + " water"
        asyncio.create_task(self._sendToClients(command))
            
    def _closeWater(self):
        command = "close valve section " + str(self.number) + " water"
        asyncio.create_task(self._sendToClients(command))
            
    def _openFertilizer(self):
        command = "open valve section " + str(self.number) + " fertilizer"
        asyncio.create_task(self._sendToClients(command))
            
    def _closeFertilizer(self):
        command = "close valve section " + str(self.number) + " fertilizer"
        asyncio.create_task(self._sendToClients(command))
            
    async def _analyze(self, humidity, moisture, light):
        current_time = datetime.now().time()        
        if self.morning_start <= current_time <= self.morning_end or self.evening_start <= current_time <= self.evening_end:
            if humidity < self.maxWateringLight and moisture < self.humidityThreshold and light < self.moistureThreshold:
                await self._openWater()
            else:
                await self._closeWater()
    
    def filterData(self, data):
        lines = data.splitlines()
        if self.mode == "Auto":
            count = 0
            humidity = moisture = light = temp = None
            line_index = 2
            
            while count < 3 and line_index < len(lines):
                current_line = lines[line_index].strip()  # Strip any leading/trailing whitespace
                
                if current_line.startswith(str(self.number)):
                    if count == 0:
                        humidity = float(current_line.split(',')[2])
                        temp = float(current_line.split(',')[1])
                        count += 1
                    elif count == 1:
                        moisture = float(current_line.split(',')[1])
                        count += 1
                    elif count == 2:
                        light = float(current_line.split(',')[1])
                        count += 1
                line_index += 1
                
            if humidity is not None and moisture is not None and light is not None and temp is not None:
                self.latestHumidity = humidity
                self.latestMoisture = moisture
                self.latestLight = light
                self.latestTemperature = temp
                asyncio.create_task(self._analyze(humidity, moisture, light))
                
    def setMode(self, mode):
        self.mode = mode
    
    def setThreshold(self, humidityThreshold, moistureThreshold, maxWateringLight):
        self.humidityThreshold = humidityThreshold
        self.moistureThreshold = moistureThreshold
        self.maxWateringLight = maxWateringLight
        
    def _convert_HM_time(self, time_string):
        return datetime.strptime(time_string, "%H:%M").time()
        
    def setTimes(self, morning_start, morning_end, evening_start, evening_end):
        self.morning_start = self._convert_to_time(morning_start)
        self.morning_end = self._convert_to_time(morning_end)
        self.evening_start = self._convert_to_time(evening_start)
        self.evening_end = self._convert_to_time(evening_end)

    def setName(self, name):
        self.name = name
    
    def getData(self):
        data = {
            "number": self.number,
            "name": self.name,
            "maxWateringLight": self.maxWateringLight,
            "humidityThreshold": self.humidityThreshold,
            "moistureThreshold": self.moistureThreshold,
            "mode": self.mode,
            "morning_start": self.morning_start.strftime("%H:%M:%S"),
            "morning_end": self.morning_end.strftime("%H:%M:%S"),
            "evening_start": self.evening_start.strftime("%H:%M:%S"),
            "evening_end": self.evening_end.strftime("%H:%M:%S"),
            "water_valve_status": self.water_valve,
            "fertilizer_valve_status": self.fertilizer_valve,
            "latestLight": self.latestLight,
            "latestHumidity": self.latestHumidity,
            "latestMoisture": self.latestMoisture,
            "latestTemperature": self.latestTemperature
        }
        return json.dumps(data, indent=4)
    
    def getName(self):
        return self.name    
    
    def getMode(self):
        return self.mode
    
    def getTimes(self):
        def format_time(value):
            return value.strftime("%H:%M") if isinstance(value, datetime.time) else value

        return [
            format_time(self.morning_start),
            format_time(self.morning_end),
            format_time(self.evening_start),
            format_time(self.evening_end),
        ]
    
    def getWaterValveStatus(self):
        return self.water_valve
    
    def getFertilizerValveStatus(self):
        return self.fertilizer_valve
        
    def manualCloseFertilizer(self):
        self._closeFertilizer()
        self.fertilizer_valve = False
        self.mode = "Manual"
        update_status()
        
    def manualCloseWater(self):
        self._closeWater()
        self.water_valve = False
        self.mode = "Manual"
        update_status()
        
    def manualOpenFertilizer(self, time):
        self.mode = "Manual"
        self.fertilizer_valve = True
        command = "manual " + str(self.number) + " fertilizer " + str(time)
        asyncio.create_task(self._sendToClients(command))
        update_status()
           
    def manualOpenWater(self, time):
        self.mode = "Manual"
        self.water_valve = True
        command = "manual " + str(self.number) + " water " + str(time)
        asyncio.create_task(self._sendToClients(command))
        update_status()
        


        



app = Flask(__name__)
CORS(app)

@app.route('/')
def loading():
    return render_template("loading.html")

@app.route('/start')
def start():
    return render_template("start.html")

@app.route('/popup')
def popup():
    return render_template("popup.html")

@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/update')
def update():
    return render_template("update.html")

# An example API route
@app.route('/status')
def status():
    return jsonify(dataSet)

# WebSocket variables
clients = set()  # Set to track connected clients

# Function to handle WebSocket connections
async def websocket_handler(websocket):
    global sections, thresholdFertilizerLevel, thresholdWaterLevel, waterLevel, fertilizerLevel, dataSet
    print("Client connected")
    clients.add(websocket)
    try:
        async for message in websocket:
            # message is come from ESP32 
            # send message to all object in array
            sendToClients(message)
            for i in sections:
                i.filterData(message)
                
            lines = message.splitlines()
            # Loop through each line and check for the keywords
            for line in lines:
                if "waterLevel" in line:
                    waterLevel = int(line.split()[1])  # Extract the value after "waterLevel"
                elif "fertilizerLevel" in line:
                    fertilizerLevel = int(line.split()[1])  # Extract the value after "fertilizerLevel"
            if waterLevel < thresholdWaterLevel or fertilizerLevel < thresholdFertilizerLevel:
                sendToClients("BuzzerLightOn")
            else:
                sendToClients("BuzzerLightOff")
                        
            update_status() #update webpage
            send_to_server("insert", dataSet)
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        clients.remove(websocket)

# Function to send data to the server
def send_to_server(path, data): 
    headers = {
        'X-CSRFToken': "csrf_token",
        'Content-Type': 'application/json',
    }
    response = requests.post("http://127.0.0.1:8000/"+path, json=data, headers=headers)
    print(f"Response from Django server: {response.status_code}, {response.reason}")
   
def createJsonData(section_no):
    global sections, thresholdWaterLevel, thresholdFertilizerLevel
    data = sections[section_no].getData()
    json_data = None
    try:
        json_data = json.loads(data)
        #print("JSON parsed successfully:", json_data)
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
    
    return json_data
    # json_data.update({
    #     "thresholdWaterLevel": thresholdWaterLevel,
    #     "thresholdFertilizerLevel": thresholdFertilizerLevel
    # })
    # send_to_server("/home", json_data)
    # home()

async def sendToClients(command):
    if clients:
            try:
                for client in clients:
                    await client.send(command)
            except websockets.exceptions.ConnectionClosed:
                print("Client disconnected")
    else:
        print("No clients connected")

def update_status():
    global dataSet
    dataSet = {"noOfSections":  str(len(sections)),
               "waterLevel": waterLevel,
               "fertilizerLevel": fertilizerLevel}
    for i in range(len(sections)):
        dataSet[str(i)] = createJsonData(i)
    dataSet.update({
        "thresholdWaterLevel": thresholdWaterLevel,
        "thresholdFertilizerLevel": thresholdFertilizerLevel
    })

async def analyzeCommand(command):
    global sections, thresholdWaterLevel, thresholdFertilizerLevel
    print("Command from Django:" , command)
    if "initialization" in command: # "initialization,5,name1,name2,name3,name4,name5"
        print("Initializing.")
        NoOfSections = int(command.split(',')[1])
        sections = []
        for i in range(NoOfSections):
            sections.append(Section(i, command.split(',')[i+2]))
        await sendToClients("NoOfSection=" + str(NoOfSections))
        update_status()
    elif "update" in command: # "update,,,5,name,humidityThreshold,moistureThreshold,maxWateringLight,mode,morning_start,morning_end,evening_start,evening_end,name2............."
        print("Updating.")
        NoOfSections = int(command.split(',')[3])
        sections = []
        for i in range(NoOfSections):
            index_of_name = 4 + (i*9)
            sections.append(Section(i, command.split(',')[index_of_name]))
            if command.split(',')[index_of_name + 1] != "":
                sections[i].update(i, command.split(',')[index_of_name], 
                                        command.split(',')[index_of_name + 1], 
                                        command.split(',')[index_of_name + 2], 
                                        command.split(',')[index_of_name + 3], 
                                        command.split(',')[index_of_name + 4], 
                                        command.split(',')[index_of_name + 5], 
                                        command.split(',')[index_of_name + 6], 
                                        command.split(',')[index_of_name + 7], 
                                        command.split(',')[index_of_name + 8])
        await sendToClients("NoOfSection=" + str(NoOfSections))
        update_status()
    elif "open water" in command: # "open water,0,10"
        print("open water.")     
        sections[int(command.split(',')[1])].manualOpenWater(int(command.split(',')[2]))        
    elif "open fertilizer" in command: # "open fertilizer,0,10"
        print("open fertilizer.")
        sections[int(command.split(',')[1])].manualOpenFertilizer(int(command.split(',')[2]))
    elif "close water" in command: # "close water,0"
        print("close water.")
        sections[int(command.split(',')[1])].manualCloseWater()
        update_status() #remove this line in production-**************************************************************************************************************************************
    elif "close fertilizer" in command: # "close fertilizer,0"
        print("close fertilizer.")
        sections[int(command.split(',')[1])].manualCloseFertilizer()
        update_status() #remove this line in production-**************************************************************************************************************************************
    elif "change name" in command: # "change name,0,name"
        print("change name.")
        sections[int(command.split(',')[1])].setName(command.split(',')[2])
        update_status()
    elif "change mode" in command: # "change mode,0,Auto"
        print("change mode.")
        sections[int(command.split(',')[1])].setMode(command.split(',')[2])
        update_status()
    elif "set times" in command: # "set times,0,morning_start,morning_end,evening_start,evening_end"
        print("set times.")
        sections[int(command.split(',')[1])].setTimes(command.split(',')[2],command.split(',')[3],command.split(',')[4],command.split(',')[5])
        update_status()
    elif "threshold" in command: # "threshold,0,humidity,soil,light"
        print("threshold.")
        sections[int(command.split(',')[1])].setThreshold(command.split(',')[2], command.split(',')[3], command.split(',')[4])
        update_status()
    elif "water" in command: # "water,0"
        print("update water.")
        thresholdWaterLevel = float(command.split(',')[1])
        update_status()
    elif "fertilizer" in command: # "fertilizer,0"
        print("update Fertilizer.")
        thresholdFertilizerLevel = float(command.split(',')[1])
        update_status()
    else:
        print("Invalid command.")
    send_to_server("insert", dataSet)

# Function to run the WebSocket server
async def start_websocket_server():
    async with websockets.serve(websocket_handler, "0.0.0.0", 8765):
        print("WebSocket server running on ws://0.0.0.0:8765")
        await asyncio.Future()  # Keep the server running


# HTTP route to control the valve (via command)
@app.route('/app', methods=['PUT'])
async def control_valve():
    print("resived")
    if request.is_json:
        command = request.json.get("command")
        print("Command:",command)
        asyncio.create_task(analyzeCommand(command))
        return jsonify({"message": "Data received", "data": command}), 200
    else:
        return jsonify({"error": "Invalid JSON data"}), 400
    
# Function to run Flask in a separate thread
def start_flask():
    app.run(host='0.0.0.0', port=5000)


# Main entry point to start both servers
if __name__ == "__main__":
    # Start Flask in a separate thread
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=False)
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.start()
    asyncio.run(start_websocket_server()) # Start the WebSocket server in the main thread's event loop
    # data1 = {
    #     "name": "Chandi"
    # }
    # while True:
    #     send_to_server("ui/sec", data1)
    #     sleep(5)

    # Start the WebSocket server in the main thread's event loop
    # asyncio.run(start_websocket_server())
    
    
