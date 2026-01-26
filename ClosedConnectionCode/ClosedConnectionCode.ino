#include "HX711.h"
#include <time.h>      
#include <sys/time.h>  
#include "BluetoothSerial.h"

// --- BLUETOOTH SETUP ---
BluetoothSerial SerialBT;
#define BT_DEVICE_NAME "ESP32_Single_Scale"

#define DOUT 22
#define CLK 23

HX711 scale;
char timeStringBuffer[32];
bool timeSynced = false;

void setup() {
  Serial.begin(115200);

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
        SerialBT.println("ACK_SYNC_SINGLE"); 
        Serial.println("Time Synced!");
      }
    } else {
      SerialBT.println("WAITING_FOR_SYNC_SINGLE");
      delay(500);
    }
  }

  // --- SENSOR SETUP ---
  scale.begin(DOUT, CLK);
  SerialBT.println("Taring... Remove any weight.");
  scale.tare(); 
  delay(2000);
  SerialBT.println("Tare complete.");
}

void loop() {
  if (!timeSynced) return;

  if (scale.is_ready()) {
    long reading = scale.read();
    
    struct timeval tv;
    gettimeofday(&tv, NULL);
    struct tm* timeinfo = gmtime(&tv.tv_sec);
    strftime(timeStringBuffer, sizeof(timeStringBuffer), "%H:%M:%S", timeinfo);
    int millisec = tv.tv_usec / 1000;

    // Print to Bluetooth
    SerialBT.printf("%s.%03d, %ld\n", timeStringBuffer, millisec, reading);
    
    // Print to USB
    Serial.printf("%s.%03d, %ld\n", timeStringBuffer, millisec, reading);

  }
  delay(100); 
}