import serial
import serial.tools.list_ports
import time
import threading
import queue
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import requests
from flask import Flask, jsonify # Import Flask and jsonify
import json
import websocket

# --- Global Variables ---
baud_rate = 38400  # IMU baud rate
ax = ay = az = gx = gy = gz = 0
s = None  # Serial port object
global retryconenction, capture_stablization, finish_stablization, crashamount, phone_imu_thread
retryconenction = True
capture_stablization = False
finish_stablization = False
phone_imu_thread = None
crashamount = 0
currentstate = "STANDYBY"

# --- Data Queue for Overlay ---
data_queue = queue.Queue()
stop_event = threading.Event()

# --- Flask App Initialization ---
app = Flask(__name__)

#Config handling
currentconfig = {}

CONFIG_FILE = 'config.json'

def read_config(value):    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config[value]
    except Exception as e:
        print(f"Error reading config.json: {e}")
        return None

def write_config(value, new_value):
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        config[value] = new_value
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error writing config.json: {e}")

def checkconfig():
    global currentconfig
    try:
        with open(CONFIG_FILE, 'r') as f:
            currentconfig = json.load(f)
    except Exception as e:
        print(f"Error reading config.json: {e}")


# --- REST API Endpoint ---

@app.route('/', methods=['GET'])
def index():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "route": str(rule),
            "methods": list(rule.methods)
        })
    return jsonify({"routes": routes})

@app.route('/imu_data', methods=['GET'])
def get_imu_data():
    """
    Returns the current IMU data as a JSON object.
    """
    imu_data = {
        "accelerometer": {
            "x": ax,
            "y": ay,
            "z": az
        },
        "gyroscope": {
            "x": gx,
            "y": gy,
            "z": gz
        },
        "status": currentstate
    }
    return jsonify(imu_data)


@app.route('/status', methods=['GET'])
def get_status():
    global currentstate
    return jsonify({"status": currentstate})

@app.route('/refreshconfig', methods=['POST'])
def refresh_config():
    checkconfig()
    return jsonify({"status": "Config Refreshed"})

@app.route('/start_calibration', methods=['POST'])
def start_calibration():
    global capture_stablization
    capture_stablization = True
    return jsonify({"status": "Calibration started"})

@app.route('/stop_calibration', methods=['POST'])
def stop_calibration():
    global capture_stablization
    finish_stablization = True
    return jsonify({"status": "Calibration stopped"})


# --- Overlay Class Definition ---
class Overlay(QtWidgets.QWidget):
    def __init__(self, data_queue, stop_event):
        super().__init__()
        self.data_queue = data_queue
        self.stop_event = stop_event
        self.imu_text = "Waiting for IMU data..."
        self.init_ui()

        # Timer to update the overlay
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_overlay_data)
        self.timer.start(50)  # Update every 50 milliseconds

    def init_ui(self):
        # Set window flags for a transparent, borderless, always-on-top window
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowDoesNotAcceptFocus |
            QtCore.Qt.WindowTransparentForInput
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Set initial geometry (can be adjusted)
        self.setGeometry(100, 500, 300, 600) # x, y, width, height

        # Create a QLabel to display the text
        self.label = QtWidgets.QLabel(self.imu_text, self)
        self.label.setAlignment(QtCore.Qt.AlignCenter)

        # Set font for better visibility
        font = QtGui.QFont("Arial", 20, QtGui.QFont.Bold)
        self.label.setFont(font)
        self.label.setStyleSheet("color: white;") # White text for contrast

        # Layout to center the label
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def paintEvent(self, event):
        # This method is called when the widget needs to be repainted
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Draw a semi-transparent background rectangle
        painter.setBrush(QtGui.QColor(0, 0, 0, 0)) # Black with 150 alpha (out of 255)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10) # Rounded corners

        # The QLabel handles drawing the text, so no need to draw text here

    def update_overlay_data(self):
        # Check if new data is available in the queue
        try:
            while True:
                new_text = self.data_queue.get_nowait()
                self.imu_text = new_text
        except queue.Empty:
            pass # No new data

        self.label.setText(self.imu_text)
        self.update() # Request a repaint

        if self.stop_event.is_set():
            self.close() # Close the overlay if stop event is set

# --- End Overlay Class Definition ---

def capture_esp32_stablization_offset(ax, ay, az, gx, gy, gz):
    print("Capturing ESP32 Stablization Offset")
    print("Not yet implemented")
    if finish_stablization:
        capture_stablization = False
        finish_stablization = False

def phisical_conenction_connect():
    if currentconfig["IMU_TYPE"] == "ESP32":
        global s
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if "USB" in p.description or "UART" in p.description or "serial" in p.description.lower() or "CP210x" in p.description or "CH340" in p.description:
                try:
                    s = serial.Serial(p.device, baud_rate, timeout=1)
                    return True
                except serial.SerialException as e:
                    print(f"Could not open serial port {p.device}: {e}")
                    return False
        print("No ESP32 serial port found.")
        return 
    elif currentconfig["IMU_TYPE"] == "Phone":
        try:
            ws = websocket.create_connection(f"ws://{currentconfig['PHONE_IP']}/sensor/connect?type=android.sensor.accelerometer")
            data = ws.recv()
            ws.close()
            return True
        except Exception as e:
            print(f"Error connecting to phone: {e}")
            return False

def phisical_conenction_update():
    global ax, ay, az, gx, gy, gz
    if currentconfig["IMU_TYPE"] == "ESP32" and s is not None:
        try:
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
        except serial.SerialException as e:
                print(f"Serial communication error: {e}")
                s.close()
                return False
        return False
    elif currentconfig["IMU_TYPE"] == "Phone":
        try:
            #Check if phone imu thread is running
            global phone_imu_thread
            if phone_imu_thread is None or not phone_imu_thread.is_alive():
                print("Starting phone IMU thread")
                phone_imu_thread = threading.Thread(target=phone_imu_thread_func)
                phone_imu_thread.daemon = True
                phone_imu_thread.start()
            return True
        except Exception as e:
            print(f"Error starting or managing phone thread {e}")
            return False

def phone_imu_thread_func():
    try:
        print("Trying to connect to phone")
        ws = websocket.create_connection(f"ws://{currentconfig['PHONE_IP']}/sensor/connect?type=android.sensor.accelerometer")
        print("Connected to phone")
    except Exception as e:
        print(f"Error connecting to phone: {e}")
        return
    ws = websocket.create_connection(f"ws://{currentconfig['PHONE_IP']}/sensor/connect?type=android.sensor.accelerometer")
    global ax, ay, az, gx, gy, gz
    try:
        while (currentconfig["IMU_TYPE"] == "Phone") and (currentstate == "RUNNING" or currentstate == "READY"):
            data = ws.recv()
            data = json.loads(data)
            values = data["values"]
            ax = int(values[0])
            ay = int(values[1])
            az = int(values[2])
            gx = 0 # There's no point in getting gyro from phone, gyro data from esp32 is just for the funnies
            gy = 0
            gz = 0
    except websocket.WebSocketConnectionClosedException:
        print("WebSocket connection closed unexpectedly.")
    except Exception as e:
        print(f"Error in phone IMU thread: {e}")
    finally:
        print("Closing phone IMU thread")
        ws.close()

def run_gui(data_queue, stop_event):
    app_qt = QtWidgets.QApplication(sys.argv) # Renamed to avoid conflict with Flask app
    overlay = Overlay(data_queue, stop_event)
    overlay.show()
    sys.exit(app_qt.exec_()) # Use app_qt here

def run_flask_app():
    """
    Runs the Flask application.
    """
    app.run(host='0.0.0.0', port=1202, debug=False) # debug=False for production

if __name__ == '__main__':
    # Load config
    checkconfig()

    # Start GUI thread
    gui_thread = threading.Thread(target=run_gui, args=(data_queue, stop_event), daemon=True)
    gui_thread.start()

    # Start Flask API thread
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()

    while True:
        try:
            # Check for esp32 connection
            if not phisical_conenction_connect():
                if currentstate != "STANDYBY":
                    currentstate = "STANDYBY"
                time.sleep(1) # Reduced sleep for quicker connection attempts
                continue
            elif currentstate == "STANDYBY":
                currentstate = "CONNECTED"
                print("IMU Connected. Current State: CONNECTED")

            # Verify the connection to esp32 is working
            if currentstate == "CONNECTED":
                if phisical_conenction_update():
                    currentstate = "READY"
                    print("IMU Data Flowing. Current State: READY")
                else:
                    print("error update")

            # Primary loop handling overlay and feeding esp32 IMU data.
            if currentstate == "READY" or currentstate == "RUNNING":
                if phisical_conenction_update():
                    # stablization calibration for esp32 IMU
                    if capture_stablization:
                        #Check to make sure were using esp32 beause using a phone is fucked :3
                        if currentconfig["IMU_TYPE"] == "ESP32":
                            capture_esp32_stablization_offset(ax, ay, az, gx, gy, gz)
                    
                    imu_display_data = (
                        f"Ax: {ax:04d}, Ay: {ay:04d}, Az: {az:04d}\n"
                        f"Gx: {gx:04d}, Gy: {gy:04d}, Gz: {gz:04d}"
                    )
                    try:
                        data_queue.put_nowait(imu_display_data)
                    except queue.Full:
                        pass # Queue is full, skip update for this cycle
                else:
                    print("Lost IMU data, retrying connection...")
                    currentstate = "STANDYBY"

            # Check for crash amount (currently not directly related to Flask)
            if crashamount > 5:
                print("Too many crashes. Exiting.")
                stop_event.set() # Signal GUI to close
                break

        except KeyboardInterrupt:
            print("\nKeyboardInterrupt detected. Exiting")
            stop_event.set() # Signal GUI to close
            currentstate = "EXIT"
            break

        except Exception as e:
            crashamount += 1
            print(f"Error: {e}")
            if crashamount > 5:
                print("Too many crashes. Exiting.")
                stop_event.set() # Signal GUI to close
                break
            print(f"Restarting in 5 seconds to hopefully recover. Crash count: {crashamount}")
            time.sleep(5) # Shorter sleep for faster recovery attempts

    print("Main application shutting down.")
    sys.exit(0) # Ensure a clean exit for the main thread