#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <BH1750.h>

#define warningBuzzerLight 13  // warning Buzzer and Light pin number

// Define DHT Sensors multiplexer control pins
#define DHTS0 5
#define DHTS1 2
#define DHTS2 15
#define DHTZ 22          // Define multiplexer data output pin
#define DHTTYPE DHT11    // Define DHT type
DHT dht(DHTZ, DHTTYPE);  // Create DHT object for reading data

// Define Soil Moisture Sensors multiplexer control pins
#define SoilS0 25
#define SoilS1 26
#define SoilS2 27
#define SoilZ 34  // Define multiplexer output pin (analog input)

#include <WiFi.h>
#include <Wire.h>
#include <WebSocketsClient.h>

//I2C multiplexer for lightSensors
#define TCA9548A_ADDRESS 0x70  // Define I2C multiplexer address
BH1750 lightSensor;            // Create BH1750 object

//Valve control pin
#define VALVE_DATA_PIN 18    // DS pin (Serial Data)
#define VALVE_CLOCK_PIN 21   // SH_CP pin (Shift Clock)
#define VALVE_LATCH_PIN 19   // ST_CP pin (Latch Clock)
byte secondIC = 0b00000000;  // All pins OFF for the second IC
byte firstIC = 0b00000000;   // Q1 ON for the first IC (connected to ESP32)

const int maxSize = 16;
unsigned long endTimes[maxSize] = {};  // Initial keys
int pinNumbers[maxSize] = {};          // Initial values
int currentSize = 0;                   // Current number of elements in the arrays

int Fertilizer_SENSOR_PIN = 12;  // Analog pin for the fertilizer sensor
int Water_SENSOR_PIN = 14;       // Analog pin for the water sensor
int NoOfSection = 1;             // Replace with number of total sections (Automatically replace)
unsigned long lastTime = 0;      // last time that send data to local server
unsigned long now;               // time now

//Wireless connection details
const char* NodeID = "HT001";                    //ID of the sensor node
const char* ssid = "SSID";                       // Replace with your Wi-Fi SSID
const char* password = "Sample";                 // Replace with your Wi-Fi password
const char* websocket_server = "192.168.8.167";  // Replace with Server IP address
const int websocket_port = 8765;

String sent_data, received_data;  //To store send data and same recive data to confirm connection

WebSocketsClient webSocket;

//Arrays manage
// Function to append key-value pair
void append(unsigned long endTime, int pinNumber) {
  if (currentSize < maxSize) {
    endTimes[currentSize] = endTime;
    pinNumbers[currentSize] = pinNumber;
    currentSize++;
  } else {
    Serial.println("Array is full, cannot append.");
  }
}

// Function to delete by index
void deleteByIndex(int index) {
  if (index >= 0 && index < currentSize) {
    for (int i = index; i < currentSize - 1; i++) {
      endTimes[i] = endTimes[i + 1];
      pinNumbers[i] = pinNumbers[i + 1];
    }
    currentSize--;  // Reduce the size after deletion
  } else {
    Serial.println("Invalid index.");
  }
}

// Function to loop through arrays
void checkTimes() {
  for (int i = 0; i < currentSize; i++) {
    if (now > endTimes[i]) {
      setValveStatus(pinNumbers[i], false);
      deleteByIndex(i);
    }
  }
}

String getTankData(int SENSOR_PIN, String type) {
  int sensorValue = analogRead(SENSOR_PIN);
  float level = map(sensorValue, 0, 4095, 0, 100);  // Map to 0-100% (adjust as needed)
  Serial.print(type);
  Serial.print(" Level: ");
  Serial.print(level);
  Serial.println(" %");
  return String(level);
}


// Function to select a channel on the 74HC4051 for DHT Sensors
void selectDHTChannel(int channel) {
  digitalWrite(DHTS0, channel & 0x01);
  digitalWrite(DHTS1, (channel >> 1) & 0x01);
  digitalWrite(DHTS2, (channel >> 2) & 0x01);
}

//DHT data management
String getDHTData(int channel, String data) {
  // Loop through the connected sensors
  for (channel; channel < NoOfSection; channel++) {  // Adjust range for the number of sensors
    selectDHTChannel(channel);                       // Select the corresponding channel
    delay(100);                                      // Allow time for the channel to stabilize

    // Read data from the DHT11 sensor
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    // Check if readings are valid
    if (isnan(temperature) || isnan(humidity)) {
      delay(2000);
      return getDHTData(channel, data);
    } else {
      data += String(channel) + "," + String(temperature) + "," + String(humidity) + "\n";
      Serial.print("Sensor ");
      Serial.print(channel);
      Serial.print(": Temp = ");
      Serial.print(temperature);
      Serial.print("°C, Hum = ");
      Serial.print(humidity);
      Serial.println("%");
    }
  }

  return data;
}

// Function to select a channel on the TCA9548A
void selectLightChannel(uint8_t channel) {
  if (channel > 7) return;  // Channel range is 0-7
  Wire.beginTransmission(TCA9548A_ADDRESS);
  Wire.write(1 << channel);  // Send channel bit to TCA9548A
  Wire.endTransmission();
}

//Light data management
String getLightData(int ch, String data) {
  // Loop through the connected sensors
  for (int channel = ch; channel < NoOfSection; channel++) {  // Adjust range for the number of sensors
    selectLightChannel(channel);                              // Select the corresponding channel
    delay(100);                                               // Allow time for the channel to stabilize

    // Read light level (lux)
    float lux = lightSensor.readLightLevel();

    // Check if readings are valid
    if (lux < 0) {
      delay(2000);
      return getLightData(channel, data);
    } else {
      data += String(channel) + "," + String(lux) + "\n";
      // Print the sensor data
      Serial.print("Channel ");
      Serial.print(channel);
      Serial.print(": Light Intensity = ");
      Serial.print(lux);
      Serial.println(" lux");
    }
  }

  return data;
}

void initializeLightSensors(uint8_t ch) {
  // Initialize BH1750 sensors on each channel
  for (uint8_t channel = ch; channel < NoOfSection; channel++) {
    selectLightChannel(channel);
    int retries = 0;
    bool lightSensorInitSuccess = false;
    do {
      lightSensorInitSuccess = lightSensor.begin(BH1750::CONTINUOUS_HIGH_RES_MODE);
      retries++;
      delay(200);
    } while (!lightSensorInitSuccess && retries < 5);
    if (retries == 5) {
      Serial.println("Failed to initialize BH1750 after retries");
      return;
    }
    Serial.print("Initialized BH1750 on section ");
    Serial.println(channel);
  }
}

// Function to select a channel on the 74HC4051 for Soil Moisture Sensors
void selectSoilChannel(int channel) {
  digitalWrite(SoilS0, channel & 0x01);
  digitalWrite(SoilS1, (channel >> 1) & 0x01);
  digitalWrite(SoilS2, (channel >> 2) & 0x01);
}

//Soil data management
String getSoilData(int channel, String data) {
  // Loop through the connected sensors
  for (channel; channel < NoOfSection; channel++) {  // Adjust range for the number of sensors
    selectSoilChannel(channel);                      // Select the corresponding channel
    delay(100);                                      // Allow time for the channel to stabilize

    // Read the soil moisture sensor value
    int sensorValue = analogRead(SoilZ);

    // Convert the raw value to a percentage (assuming 0-4095 ADC range for ESP32)
    float moisturePercent = map(sensorValue, 4095, 0, 0, 100);

    // Check if readings are valid
    if (isnan(moisturePercent)) {
      delay(2000);
      return getSoilData(channel, data);
    } else {
      data += String(channel) + "," + String(moisturePercent) + "\n";
      // Print the sensor data
      Serial.print("Sensor ");
      Serial.print(channel);
      Serial.print(": Raw Value = ");
      Serial.print(sensorValue);
      Serial.print(", Moisture = ");
      Serial.print(moisturePercent);
      Serial.println("%");
    }
  }

  return data;
}

void sentToLocalSever() {
  lastTime = millis();

  String dhtData = getDHTData(0, "");
  String soilData = getSoilData(0, "");
  uint8_t channel = 0;
  String lightData = getLightData(channel, "");

  if (dhtData == "" || soilData == "" || lightData == "") {
    Serial.println(F("Failed reception"));
    return;
    // Returns an error if the ESP32 does not receive any measurements
  }
  String data = String(NodeID) + "\n" + String(NoOfSection) + "\n" + String(firstIC) + "\n" + String(secondIC) + "\n" + dhtData + "" + soilData + "" + lightData + "waterlevel " + getTankData(Water_SENSOR_PIN, "Water") + "\nfertilizerLevel " + getTankData(Fertilizer_SENSOR_PIN, "Fertilizer");
  sent_data = data;
  webSocket.sendTXT(data);
  // Transmits the received measurements to the serial terminal via USB
}

//open or close specifics valve
void setValveStatus(int outputPin, bool state) {
  // Update the corresponding bit in currentState
  if (outputPin < 8) {
    if (state) {
      firstIC |= (1 << outputPin);  // Set the bit to HIGH
    } else {
      firstIC &= ~(1 << outputPin);  // Clear the bit to LOW
    }
  } else if (outputPin < 16) {
    if (state) {
      secondIC |= (1 << (outputPin - 8));  // Set the bit to HIGH
    } else {
      secondIC &= ~(1 << (outputPin - 8));  // Clear the bit to LOW
    }
  }

  // Send the updated state to the 74HC595
  digitalWrite(VALVE_LATCH_PIN, LOW);                             // Disable output updates
  shiftOut(VALVE_DATA_PIN, VALVE_CLOCK_PIN, MSBFIRST, secondIC);  // Send data to the second IC
  shiftOut(VALVE_DATA_PIN, VALVE_CLOCK_PIN, MSBFIRST, firstIC);   // Send data to the first IC
  digitalWrite(VALVE_LATCH_PIN, HIGH);                            // Latch the output

  sentToLocalSever();
}

void setPinMode() {
  // Set up multiplexer control pins
  pinMode(DHTS0, OUTPUT);
  pinMode(DHTS1, OUTPUT);
  pinMode(DHTS2, OUTPUT);

  // Set up multiplexer control pins
  pinMode(SoilS0, OUTPUT);
  pinMode(SoilS1, OUTPUT);
  pinMode(SoilS2, OUTPUT);

  pinMode(warningBuzzerLight, OUTPUT);

  pinMode(VALVE_DATA_PIN, OUTPUT);
  pinMode(VALVE_CLOCK_PIN, OUTPUT);
  pinMode(VALVE_LATCH_PIN, OUTPUT);
}

int getPinNumber(int section, String type) {
  if (type == "water") {
    return section * 2;
  } else if (type == "fertilizer") {
    return section * 2 + 1;
  }
}

// Check if the command contains "open" or "close"
bool getState(String command) {
  return command.indexOf("open") != -1;
}

// Extract the section number
int getSection(String command) {
  int sectionIndex = command.indexOf("section ");
  if (sectionIndex != -1) {
    return command.substring(sectionIndex + 8, command.indexOf(" ", sectionIndex + 8)).toInt();
  }
  return -1;
}

// Check if the command pertains to "water" or "fertilizer"
String getType(String command) {
  if (command.indexOf("water") != -1) {
    return "water";
  } else if (command.indexOf("fertilizer") != -1) {
    return "fertilizer";
  }
}

void valveStatusChange(String command) {
  bool state = getState(command);               // To store "open"=true or "close"=false
  int section = getSection(command);            // To store the section number
  String type = getType(command);               // To store "water" or "fertilizer"
  int pinNumber = getPinNumber(section, type);  //IC number of sensor

  // Print the extracted values
  Serial.print("State: ");
  Serial.println(state);
  Serial.print("Section: ");
  Serial.println(section);
  Serial.print("Type: ");
  Serial.println(type);

  setValveStatus(pinNumber, state);
}

void valveStatusChangeManual(String data) {
  int firstSpace = data.indexOf(' ');
  int secondSpace = data.indexOf(' ', firstSpace + 1);
  int thirdSpace = data.indexOf(' ', secondSpace + 1);

  // Extract values
  int section = data.substring(firstSpace + 1, secondSpace).toInt();  // To store the section number
  String type = data.substring(secondSpace + 1, thirdSpace);          // To store "water" or "fertilizer"
  long time = data.substring(thirdSpace + 1).toInt();                 // To store intervel
  int pinNumber = getPinNumber(section, type);                        //IC number of sensor

  // Print the extracted values
  Serial.print("Semi Auto ");
  Serial.print("Section: ");
  Serial.println(section);
  Serial.print("time: ");
  Serial.println(time);
  Serial.print("Type: ");
  Serial.println(type);


  setValveStatus(pinNumber, true);
  append(now + time, pinNumber);
}

void webSocketEvent(WStype_t type, uint8_t* payload, size_t lenght) {
  String command = String((char*)payload);
  switch (type) {
    case WStype_CONNECTED:
      Serial.println("Connected to WebSocket server");
      // Send a message to the server
      break;
    case WStype_DISCONNECTED:
      Serial.println("Disconnected from WebSocket server");
      break;
    case WStype_TEXT:
      //* Here write to instruction to
      //* based on the receive command, switch o/off the LED
      if (sent_data == command) {
        received_data = command;
      } else if (command == "BuzzerLightOff") {
        digitalWrite(warningBuzzerLight, LOW);
      } else if (command == "BuzzerLightOn") {
        digitalWrite(warningBuzzerLight, HIGH);
      } else if (command.indexOf("NoOfSection") != -1) {
        NoOfSection = command.substring(12).toInt();  // command = "NoOfSection=5";
      } else if (command.indexOf("manual") != -1) {
        valveStatusChangeManual(command);  // command = "manual 3 water 10";
      } else {
        valveStatusChange(command);
      }
      Serial.print("Command receive: ");
      Serial.println(command);
      break;
    case WStype_ERROR:
      Serial.println("Error in WebSocket connection");
      break;
    default:
      break;
  }
}

void startWiFiandWebSocket() {
  WiFi.begin(ssid, password);
  Serial.print("connecting to wifi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.print("connected to wifi...");
  Serial.println(WiFi.localIP());
  //initialize the webSocket
  webSocket.begin(websocket_server, websocket_port, "/");
  webSocket.onEvent(webSocketEvent);
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);

  setPinMode();

  // Initialize the DHT sensor
  dht.begin();

  // Initialize I2C communication
  Wire.begin(32, 35);  // SDA on GPIO32, SCL on GPIO35
  uint8_t channel = 0;
  initializeLightSensors(channel);

  startWiFiandWebSocket();
}

void loop() {
  // put your main code here, to run repeatedly:
  webSocket.loop();
  // Send periodic messages to the server
  lastTime = 0;
  now = millis();
  if (now - lastTime > 300000) {  // Every 300 seconds
    sentToLocalSever();
  }

  if (now - lastTime > 30000) {  // after 30 second
    if (sent_data != received_data) {
      digitalWrite(warningBuzzerLight, HIGH);
    }
  }

  checkTimes();
}

