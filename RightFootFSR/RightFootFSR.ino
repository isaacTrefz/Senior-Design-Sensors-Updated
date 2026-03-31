#include <time.h>      
#include <sys/time.h>  
#include "BluetoothSerial.h"

// --- BLUETOOTH SETUP ---
BluetoothSerial SerialBT;
#define BT_DEVICE_NAME "ESP32_Right_Foot"

// --- PIN CONFIGURATION ---
const int FSR1 = 32;
const int FSR2 = 33;
const int FSR3 = 34;
const int FSR4 = 35;

char timeStringBuffer[32];
bool timeSynced = false;

void setup() {
  Serial.begin(115200);
  
  // ADC Configuration
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  // Initialize Bluetooth
  SerialBT.begin(BT_DEVICE_NAME);
  Serial.println("Bluetooth Started. Pair with: " BT_DEVICE_NAME);

  // --- WAIT FOR SYNC ---
  Serial.println("Waiting for Time Sync from Laptop...");

  while (!timeSynced) {
    if (SerialBT.available()) {
      String incoming = SerialBT.readStringUntil('\n');
      incoming.trim();

      if (incoming.startsWith("SYNC:")) {
        long timestamp = incoming.substring(5).toInt();

        struct timeval now = { .tv_sec = (time_t)timestamp, .tv_usec = 0 };
        settimeofday(&now, NULL);
        
        timeSynced = true;
        SerialBT.println("ACK_SYNC_RIGHT"); 
        Serial.println("Time Synced!");
      }
    } else {
      SerialBT.println("WAITING_FOR_SYNC_RIGHT");
      delay(500);
    }
  }

  SerialBT.println("Time,FSR1_Raw,FSR2_Raw,FSR3_Raw,FSR4_Raw");
}

void loop() {
  if (!timeSynced) return;

  int raw1 = analogRead(FSR1);
  int raw2 = analogRead(FSR2);
  int raw3 = analogRead(FSR3);
  int raw4 = analogRead(FSR4);
  
  struct timeval tv;
  gettimeofday(&tv, NULL);
  struct tm* timeinfo = gmtime(&tv.tv_sec);
  strftime(timeStringBuffer, sizeof(timeStringBuffer), "%H:%M:%S", timeinfo);
  int millisec = tv.tv_usec / 1000;

  // Print to Bluetooth
  SerialBT.printf("%s.%03d, %d, %d, %d, %d\n", timeStringBuffer, millisec, raw1, raw2, raw3, raw4);

  // Print to USB (Debugging)
  Serial.printf("%s.%03d, %d, %d, %d, %d\n", timeStringBuffer, millisec, raw1, raw2, raw3, raw4);

  delay(50); 
}