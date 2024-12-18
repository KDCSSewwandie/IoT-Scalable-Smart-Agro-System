# Generated by Django 5.1.3 on 2024-12-04 13:41

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LandData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('time', models.TimeField(auto_now_add=True)),
                ('noOfSections', models.IntegerField(max_length=10)),
                ('waterLevel', models.DecimalField(decimal_places=0, max_digits=3)),
                ('waterThreshold', models.DecimalField(decimal_places=0, max_digits=3)),
                ('fertilizerLevel', models.DecimalField(decimal_places=0, max_digits=3)),
                ('fertilizerThreshold', models.DecimalField(decimal_places=0, max_digits=3)),
            ],
        ),
        migrations.CreateModel(
            name='Sections',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=3)),
                ('name', models.CharField(max_length=255)),
                ('maxWateringLight', models.CharField(max_length=10)),
                ('humidityThreshold', models.CharField(max_length=3)),
                ('moistureThreshold', models.CharField(max_length=10)),
                ('mode', models.CharField(max_length=6)),
                ('morning_start', models.CharField(max_length=8)),
                ('morning_end', models.CharField(max_length=8)),
                ('evening_start', models.CharField(max_length=8)),
                ('evening_end', models.CharField(max_length=8)),
                ('water_valve_status', models.CharField(max_length=10)),
                ('fertilizer_valve_status', models.CharField(max_length=10)),
                ('latestLight', models.CharField(max_length=10)),
                ('latestHumidity', models.CharField(max_length=3)),
                ('latestMoisture', models.CharField(max_length=10)),
                ('latestTemperature', models.CharField(max_length=10)),
                ('date', models.DateField(auto_now_add=True)),
                ('time', models.TimeField(auto_now_add=True)),
            ],
        ),
    ]