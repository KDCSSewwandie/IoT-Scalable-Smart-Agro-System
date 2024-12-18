from django.db import models

class LandData(models.Model):
    date = models.DateField(auto_now_add=True)  # Automatically set the date when a new row is created
    time = models.TimeField(auto_now_add=True)  # Automatically set the time when a new row is created
    noOfSections = models.IntegerField(max_length=10)
    waterLevel = models.DecimalField(max_digits=3, decimal_places=0)
    waterThreshold = models.DecimalField(max_digits=3, decimal_places=0)
    fertilizerLevel = models.DecimalField(max_digits=3, decimal_places=0)
    fertilizerThreshold = models.DecimalField(max_digits=3, decimal_places=0)

    def __str__(self):
        return f"Tanks on {self.date} at {self.time}"
    
class Sections(models.Model):
    date = models.DateField(auto_now_add=True)  # Automatically set the date when a new row is created
    time = models.TimeField(auto_now_add=True)  # Automatically set the time when a new row is created
    number = models.CharField(max_length=3)
    name = models.CharField(max_length=255)
    maxWateringLight = models.CharField(max_length=10)
    humidityThreshold = models.CharField(max_length=3)
    moistureThreshold = models.CharField(max_length=10)
    mode = models.CharField(max_length=6)
    morning_start = models.CharField(max_length=8)
    morning_end = models.CharField(max_length=8)
    evening_start = models.CharField(max_length=8)
    evening_end = models.CharField(max_length=8)
    water_valve_status = models.CharField(max_length=10)
    fertilizer_valve_status = models.CharField(max_length=10)
    latestLight = models.CharField(max_length=10)
    latestHumidity = models.CharField(max_length=3)
    latestMoisture = models.CharField(max_length=10)
    latestTemperature = models.CharField(max_length=10)

    def __str__(self):
        return f"Section {self.name} on {self.date} at {self.time}"