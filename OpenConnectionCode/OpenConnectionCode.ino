#include "HX711.h"
#include <time.h>      
#include <sys/time.h>
#include "BluetoothSerial.h" // [cite: 1]
#include "Wire.h"            // [cite: 1]

// --- BLUETOOTH SETUP ---
BluetoothSerial SerialBT;
#define BT_DEVICE_NAME "ESP32_Multi_Scale" // 

// --- PIN CONFIGURATION ---
// SCALES
#define DOUT1 22 //  WARNING: Check for conflict if using standard I2C (SCL=22)
#define CLK1  23
#define DOUT2 18 
#define CLK2  19 

// ANALOG
#define ANALOG_PIN_1 32 
#define ANALOG_PIN_2 33 
#define ANALOG_PIN_3 34 
#define ANALOG_PIN_4 35 

// MPU-6050 (GY-521)
// TODO: ENTER YOUR PINS BELOW
const int I2C_SDA = 21; // [cite: 1] User to fill in
const int I2C_SCL = 3; // [cite: 2] User to fill in
const int MPU_ADDR = 0x68; // [cite: 2]

// --- GLOBALS ---
HX711 scale1;
HX711 scale2; // [cite: 13]

char timeStringBuffer[32];
bool timeSynced = false;

// MPU Variables
int16_t accel_x, accel_y, accel_z;

void setup() {
  Serial.begin(115200);
  
  // Initialize Bluetooth
  SerialBT.begin(BT_DEVICE_NAME);
  Serial.println("Bluetooth Started. Pair with: " BT_DEVICE_NAME); // [cite: 14]

  // --- WAIT FOR SYNC ---
  Serial.println("Waiting for Time Sync from Laptop...");
  while (!timeSynced) { // [cite: 15]
    if (SerialBT.available()) {
      String incoming = SerialBT.readStringUntil('\n');
      incoming.trim();
      // Expected format: "SYNC:<unix_timestamp_seconds>"
      if (incoming.startsWith("SYNC:")) { // [cite: 16]
        long timestamp = incoming.substring(5).toInt();
        struct timeval now = { .tv_sec = (time_t)timestamp, .tv_usec = 0 }; // [cite: 17]
        settimeofday(&now, NULL); // [cite: 18]
        
        timeSynced = true;
        SerialBT.println("ACK_SYNC_MULTI");
        Serial.println("Time Synced!");
      }
    } else {
      SerialBT.println("WAITING_FOR_SYNC_MULTI");
      delay(500); // [cite: 20]
    }
  }

  // --- SENSOR SETUP ---
  
  // 1. Scales
  scale1.begin(DOUT1, CLK1);
  scale2.begin(DOUT2, CLK2);

  // 2. MPU-6050
  // Initialize I2C with user-defined pins
  Wire.begin(I2C_SDA, I2C_SCL); // [cite: 4]
  Wire.beginTransmission(MPU_ADDR); // [cite: 5]
  Wire.write(0x6B); // PWR_MGMT_1 register
  Wire.write(0);    // Wake up MPU-6050
  Wire.endTransmission(true);
  Serial.println("MPU-6050 Initialized");

  // Tare Scales
  SerialBT.println("Taring scales... Remove any weight.");
  scale1.tare(); // [cite: 21]
  scale2.tare();
  delay(2000);
  SerialBT.println("Tare complete.");
  
  // Header
  // Updated to include Acceleration columns
  SerialBT.println("Time,Scale1,Scale2,Analog1,Analog2,Analog3,Analog4,AccelX,AccelY,AccelZ");
}

void loop() {
  if (!timeSynced) return;

  // Check if scales are ready
  bool s1_ready = scale1.is_ready();
  bool s2_ready = scale2.is_ready(); // [cite: 22]

  if (s1_ready && s2_ready) {
    // 1. Read Scales
    long reading1 = scale1.read();
    long reading2 = scale2.read();

    // 2. Read Analog
    int ana1 = analogRead(ANALOG_PIN_1);
    int ana2 = analogRead(ANALOG_PIN_2); // [cite: 24]
    int ana3 = analogRead(ANALOG_PIN_3);
    int ana4 = analogRead(ANALOG_PIN_4);

    // 3. Read MPU-6050 Acceleration
    Wire.beginTransmission(MPU_ADDR);
    Wire.write(0x3B); // Starting register for Accel Readings 
    Wire.endTransmission(false);
    // Request 6 bytes (2 bytes per axis: X, Y, Z)
    Wire.requestFrom(MPU_ADDR, 6, true); 
    
    if (Wire.available() >= 6) {
        accel_x = Wire.read() << 8 | Wire.read();
        accel_y = Wire.read() << 8 | Wire.read();
        accel_z = Wire.read() << 8 | Wire.read(); // [cite: 7]
    }

    // 4. Get Time
    struct timeval tv;
    gettimeofday(&tv, NULL); 
    struct tm* timeinfo = gmtime(&tv.tv_sec);
    strftime(timeStringBuffer, sizeof(timeStringBuffer), "%H:%M:%S", timeinfo);
    int millisec = tv.tv_usec / 1000;
    // 5. Print to Bluetooth
    SerialBT.printf("%s.%03d, %ld, %ld, %d, %d, %d, %d, %d, %d\n", 
                  timeStringBuffer, millisec, 
                  (reading1+ reading2), 
                  ana1, ana2, ana3, ana4,
                  accel_x, accel_y, accel_z);

    // 6. Print to USB (Debugging)
    Serial.printf("%s.%03d, %ld, %ld, %d, %d, %d, %d, %d, %d\n", 
                  timeStringBuffer, millisec, 
                  (reading1 + reading2), 
                  ana1, ana2, ana3, ana4,
                  accel_x, accel_y, accel_z);

  } else {
     // Optional heartbeat
  }
  
  delay(100); // 10Hz Sample Rate 
}