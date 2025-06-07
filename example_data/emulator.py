# Emulates an ESP32 device on a virtual serial port (for Linux) and provides IMU data from a log file.
import time
import sys
import os
import serial

# --- Configuration ---
# IMPORTANT: Change this to one of the ports created by socat.
# Your other application will connect to the OTHER port in the pair.
EMULATOR_PORT_NAME = '/dev/pts/2'  # <-- CHANGE THIS BASED ON SOCAT'S OUTPUT
baud_rate = 38400  # The baud rate your other application expects

# --- Main Emulation Logic ---

# 1. Check directory for log files
availablelogs = [file for file in os.listdir(".") if file.lower().endswith(".txt")]

if not availablelogs:
    print("No log files (.txt) found in the current directory. Exiting...")
    exit()

# 2. Select log file from a list
while True:
    print("\nPlease select a log file to use for emulation:")
    for i, log in enumerate(availablelogs):
        print(f"  {i+1}. {log}")
    selection = input("Enter the number of the log file: ")
    if selection.isdigit() and 1 <= int(selection) <= len(availablelogs):
        selectedlog = availablelogs[int(selection) - 1]
        break
    else:
        print("Invalid selection. Please try again.")

# 3. Load log file data
try:
    with open(selectedlog, "r") as f:
        lines = f.readlines()
    print(f"Loaded {len(lines)} lines from {selectedlog}")
except FileNotFoundError:
    print(f"Error: Log file '{selectedlog}' not found. Exiting.")
    exit()

# 4. Start the emulator
s = None
try:
    print(f"\nAttempting to start emulator on port {EMULATOR_PORT_NAME} at {baud_rate} baud.")
    # Open the virtual serial port. This script will now act like a device.
    s = serial.Serial(EMULATOR_PORT_NAME, baud_rate, timeout=1)
    
    print(f"Emulator running. Your other application can now connect to the paired port.")
    print("Press Ctrl+C to stop.")

    # Loop forever, streaming the log data
    while True:
        for line in lines:
            line = line.strip()
            if not line:
                continue
            

            # This is the data that will be sent over the serial port
            # We add a newline character (\n) so the receiving application knows when a message ends.
            output_data = line + '\n'
            
            # Write the data to the serial port, encoded as bytes
            s.write(output_data.encode('utf-8'))
            
            # Print to the console so you can see what the emulator is doing
            print(f"Sent: {line.strip()}")
            
            # Wait a short period to simulate a real device's data rate
            time.sleep(0.02)
        
        print("--- End of log file reached. Restarting stream. ---")
        time.sleep(1)

except serial.SerialException as e:
    print(f"\nERROR: Could not open serial port '{EMULATOR_PORT_NAME}'.")
    print("Please ensure that:")
    print("1. You are running 'socat' in another terminal to create the virtual port pair.")
    print(f"2. '{EMULATOR_PORT_NAME}' exactly matches one of the ports from the socat output.")
    print("3. You have the necessary permissions to access the port (you may need to run as root or be in the 'dialout' group).")
    print(f"Details: {e}")
    sys.exit()
except KeyboardInterrupt:
    print("\nEmulator stopped by user.")
finally:
    # Ensure the serial port is closed when the script is done
    if s and s.is_open:
        s.close()
        print(f"Serial port {EMULATOR_PORT_NAME} closed.")