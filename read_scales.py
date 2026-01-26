import serial
import serial.tools.list_ports
import time
import threading
import sys

# Configuration
BAUD_RATE = 115200

# File Configuration
# These files will be created (or overwritten) when the script starts
OUTPUT_FILES = {
    "MULTI_SCALE": "multi_scale_data.csv",
    "SINGLE_SCALE": "single_scale_data.csv"
}

# CSV Headers
# Updated: Removed 'Scale2' from the MULTI_SCALE header
CSV_HEADERS = {
    "MULTI_SCALE": "Time, Scale1, Analog1, Analog2, Analog3, Analog4",
    "SINGLE_SCALE": "Time, Weight"
}

# To store connected devices
connected_devices = {}

def handle_device(ser, device_name):
    """
    Reads lines from a connected serial port.
    - Appends ALL lines to the specific CSV file.
    - Prints only every 20th line to the console to reduce clutter.
    """
    print(f"[{device_name}] Connected. Logging to {OUTPUT_FILES[device_name]}...")
    
    target_file = OUTPUT_FILES.get(device_name)
    line_count = 0  # Initialize counter

    try:
        while True:
            if ser.in_waiting:
                try:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        # --- Write to CSV (ALWAYS) ---
                        if target_file:
                            with open(target_file, "a") as f:
                                f.write(f"{line}\n")

                        # --- Print to console (CONDITIONAL) ---
                        if line_count % 20 == 0:
                            print(f"[{device_name}] {line}")
                        
                        line_count += 1
                                
                except UnicodeDecodeError:
                    pass # Ignore noise
            time.sleep(0.01)
    except serial.SerialException:
        print(f"[{device_name}] Disconnected.")
    except Exception as e:
        print(f"[{device_name}] Error: {e}")

def attempt_handshake(port):
    """
    Tries to open a COM port, listen for the 'WAITING_FOR_SYNC' message,
    and if found, sends the current time to sync the RTC.
    """
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=2)
        start_check = time.time()
        device_type = None
        
        print(f"Scanning {port}...")
        
        while (time.time() - start_check) < 3.0:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                
                if "WAITING_FOR_SYNC_MULTI" in line:
                    device_type = "MULTI_SCALE"
                    break
                elif "WAITING_FOR_SYNC_SINGLE" in line:
                    device_type = "SINGLE_SCALE"
                    break
        
        if device_type:
            current_time = int(time.time())
            cmd = f"SYNC:{current_time}\n"
            ser.write(cmd.encode())
            print(f"Found {device_type} on {port}. Sync command sent.")
            
            time.sleep(1) 
            
            t = threading.Thread(target=handle_device, args=(ser, device_type))
            t.daemon = True
            t.start()
            
            connected_devices[port] = device_type
            return True
        else:
            ser.close()
            return False

    except Exception:
        return False

def main():
    print("--- Bluetooth Scale Data Logger ---")
    
    print("Initializing CSV files...")
    for dev_type, filename in OUTPUT_FILES.items():
        try:
            with open(filename, "w") as f:
                f.write(CSV_HEADERS[dev_type] + "\n")
            print(f"Created {filename}")
        except Exception as e:
            print(f"Error creating {filename}: {e}")

    print("Scanning for devices... (Press Ctrl+C to stop)")
    
    while True:
        try:
            ports = serial.tools.list_ports.comports()
            for port_info in ports:
                port = port_info.device
                if port not in connected_devices:
                    attempt_handshake(port)
            
            time.sleep(2)
            if len(connected_devices) == 2:
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nStopping...")
            break

if __name__ == "__main__":
    main()