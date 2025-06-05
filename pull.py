#very patchy script to log IMU data

import serial
import serial.tools.list_ports
import time
import threading
import queue
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

baud_rate = 38400  # IMU baud rate
ax = ay = az = gx = gy = gz = 0
s = None
retryconenction = True

# Write new log note
print(f"START {time.time()}")
with open("logs.txt", "a") as f:
    f.write(f"START {time.time()}\n")

def phisical_conenction_connect():
    global s
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "USB" in p.description or "UART" in p.description or "serial" in p.description.lower() or "CP210x" in p.description or "CH340" in p.description:
            try:
                s = serial.Serial(p.device, baud_rate, timeout=1)
                print(f"Connected to ESP32 on {p.device}")
                return True
            except serial.SerialException as e:
                print(f"Could not open serial port {p.device}: {e}")
                return False
    print("No ESP32 serial port found.")
    return False

def phisical_conenction_update():
    global ax, ay, az, gx, gy, gz
    if s and s.is_open:
        try:
            if s.in_waiting > 0:
                line = s.readline().decode('utf-8').strip()
                if line:
                    data = line.split('\t')
                    if len(data) == 6:
                        try:
                            ax = int(data[0])
                            ay = int(data[1])
                            az = int(data[2])
                            gx = int(data[3])
                            gy = int(data[4])
                            gz = int(data[5])
                            return True
                        except ValueError:
                            print(f"Error parsing data: {line}")
                    else:
                        print(f"Received malformed line or incomplete: {line}")
                        pass
            return False
        except serial.SerialException as e:
            print(f"Serial communication error: {e}")
            s.close()
            return False
    return False

if phisical_conenction_connect():
    while True:
        try:
            if phisical_conenction_update():
                print(f"Accel(x,y,z): ({ax}, {ay}, {az})  Gyro(x,y,z): ({gx}, {gy}, {gz}), Time: {time.time()}")
                #Log to logs.txt
                with open("logs.txt", "a") as f:
                    f.write(f"Accel(x,y,z): ({ax}, {ay}, {az})  Gyro(x,y,z): ({gx}, {gy}, {gz}), Time: {time.time()}\n")
               # time.sleep(0.02) # Logging data is captured as fast as possible and is slowed down in post.
        
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt detected. Exiting...")
            break

        except Exception as e:
            print("Error while reading serial data. error:", e)
            with open("logs.txt", "a") as f:
                f.write(f"ERROR: {e}\n")
            print("Attempting to reconnect...")
            while not phisical_conenction_connect():
                print("Failed to reconnect. Retrying in 5 seconds...")
                time.sleep(5)
else:
    print("Failed to connect to ESP32. Exiting...")