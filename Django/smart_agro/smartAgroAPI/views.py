from django.shortcuts import render
from django.http import JsonResponse
from django.shortcuts import render
import requests
from .models import *
import json
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime


def loading(request):
    delete_all_land_data()
    return render(request, 'loading.html')

@csrf_exempt
def insertData(request):
    if request.method == 'POST':
        # Parse the JSON data sent in the request
        data = json.loads(request.body)

        # Now, `data` will contain the sent JSON object
        print("Received data:", data)

        # Call your function to insert the data into the database
        insert_data(data)

        return JsonResponse({'message': 'Data inserted successfully'}, status=200)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def showHistory(request):
    # Get the data from LandData and Sections models
    land_data = LandData.objects.all()  # Or use specific filters if needed
    sections_data = Sections.objects.all()  # Or use specific filters if needed
    
    # Render the template with the data
    return render(request, 'history.html', {'land_data': land_data, 'sections_data': sections_data})

def start(request):
    try:
        if is_land_data_exists():
            data = generate_data()
            if(data):
                if send_command(data):
                    return render(request, 'home.html')
        else:
            return render(request, 'start.html')
    except():
        return render(request, 'start.html')

def update(request):
    return render(request, 'update.html')
 
def home(request):
    land_data = LandData.objects.all()  # Or use specific filters if needed
    sections_data = Sections.objects.all()
    return render(request, 'home.html', {'land_data': land_data, 'sections_data': sections_data})

def homeWithoutFetch(request):
    return render(request, 'home.html')
 
def get_db_status():
    url = 'http://192.168.1.166:5000/status'  # The endpoint you're requesting from
    
    try:
        # Send a GET request to the endpoint
        response = requests.get(url)
        
        # Check if the request was successful (HTTP status code 200)
        if response.status_code == 200:
            data = response.json()  # Parse the JSON response
            return JsonResponse(data)  # Return the JSON data as a JsonResponse
        else:
            return JsonResponse({'error': 'Failed to fetch data'}, status=response.status_code)
    
    except requests.exceptions.RequestException as err:
        # Catch any errors and return an error message
        return JsonResponse({'error': str(err)}, status=500)
    
def is_land_data_exists():
    # Check if there is any data in the LandData table
    try:
        # Count the rows in the table
        row_count = LandData.objects.count()
        return row_count > 0
    except Exception as e:
        print(f"Error checking LandData: {e}")
        return False

def send_command(sendData):
    url = 'http://192.168.1.166:5000/app'  # The endpoint you're sending the PUT request to
    data = {"command": sendData}  # Replace this with the actual data you want to send
    
    try:
        # Send the PUT request with the JSON body
        response = requests.put(url, json=data, headers={"Content-Type": "application/json"})
        
        # Check if the response was successful (HTTP status code 200)
        if response.ok:
            return True  # Redirect to the home page (equivalent to window.location.href = '/home')
        else:
            # If the request fails, you can return an error message
            print(JsonResponse({"error": "Failed to send data"}, status=response.status_code))
            return False
    
    except requests.exceptions.RequestException as err:
        # Handle any exceptions that occur during the request
        print(JsonResponse({"error": str(err)}, status=500))
        return False
    
def generate_data():
    try:
        # Get the last row of LandData to determine numSections
        last_land_data = LandData.objects.last()  # Get the last entry in LandData table
        numSections = last_land_data.noOfSections  # Get the number of sections from the last row of LandData
        
        # Get the last 'numSections' rows from the Sections table
        sections = Sections.objects.all().order_by('-id')[:numSections]  # Fetch the last 'numSections' records

        # Start constructing the data string
        data = f"update,{last_land_data.waterThreshold},{last_land_data.fertilizerThreshold},{numSections}"
        
        # Iterate over the fetched sections and append data
        for section in sections:
            data += f",{section.name},{section.humidityThreshold},{section.moistureThreshold},{section.maxWateringLight},{section.mode},{section.morning_start},{section.morning_end},{section.evening_start},{section.evening_end}"

        # Return the generated data string as a JsonResponse
        return data

    except Exception as e:
        print(JsonResponse({"error": str(e)}, status=500))
        return False


def insert_data(data):
    # Extract LandData information
    land_data = {
        'waterLevel': data['waterLevel'],
        'waterThreshold': data['thresholdWaterLevel'],
        'fertilizerLevel': data['fertilizerLevel'],
        'fertilizerThreshold': data['thresholdFertilizerLevel'],
        'noOfSections': data['noOfSections'],
        'date': datetime.now().date(),
        'time': datetime.now().time(),
    }

    # Create a new LandData entry
    new_land_data = LandData.objects.create(**land_data)

    # Extract Sections data and insert
    sections_data = data  # Data already contains sections

    for section in sections_data.values():
        if isinstance(section, dict):  # Ensure we only deal with the sections data
            section_data = {
                'date': datetime.now().date(),
                'time': datetime.now().time(),
                'number': section['number'],
                'name': section['name'],
                'maxWateringLight': section['maxWateringLight'],
                'humidityThreshold': section['humidityThreshold'],
                'moistureThreshold': section['moistureThreshold'],
                'mode': section['mode'],
                'morning_start': section['morning_start'],
                'morning_end': section['morning_end'],
                'evening_start': section['evening_start'],
                'evening_end': section['evening_end'],
                'water_valve_status': section['water_valve_status'],
                'fertilizer_valve_status': section['fertilizer_valve_status'],
                'latestLight': section['latestLight'],
                'latestHumidity': section['latestHumidity'],
                'latestMoisture': section['latestMoisture'],
                'latestTemperature': section['latestTemperature'],
            }
            
            # Create new Sections entry and associate it with the created LandData entry
            new_section = Sections.objects.create(**section_data)

    return f"Inserted LandData with ID {new_land_data.id} and Sections successfully!"


def delete_all_land_data():
    LandData.objects.all().delete()
    return JsonResponse({'message': 'All LandData deleted successfully'})
    
    
