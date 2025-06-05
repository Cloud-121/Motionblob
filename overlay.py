import serial
import serial.tools.list_ports
import time
import threading
import queue
import sys
from PyQt5 import QtCore, QtGui, QtWidgets

baud_rate = 38400  # IMU baud rate
ax = ay = az = gx = gy = gz = 0
s = None  # Serial port object
retryconenction = True
crashamount = 0
currentstate = "STANDYBY"

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
            QtCore.Qt.X11BypassWindowManagerHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Set initial geometry (can be adjusted)
        self.setGeometry(100, 100, 600, 100) # x, y, width, height

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
        painter.setBrush(QtGui.QColor(0, 0, 0, 150)) # Black with 150 alpha (out of 255)
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

    def mousePressEvent(self, event):
        # Allow dragging the window
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        # Allow dragging the window
        delta = QtCore.QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

# --- End Overlay Class Definition ---


def phisical_conenction_connect():
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

def run_gui(data_queue, stop_event):
    app = QtWidgets.QApplication(sys.argv)
    overlay = Overlay(data_queue, stop_event)
    overlay.show()
    sys.exit(app.exec_())


    data_queue = queue.Queue()
    stop_event = threading.Event()

    # Start GUI thread
    gui_thread = threading.Thread(target=run_gui, args=(data_queue, stop_event), daemon=True)
    gui_thread.start()

while True:
    while True:
        try:
            #Check for esp32 conenction
            if not phisical_conenction_connect():
                if currentstate != "STANDYBY":
                    currentstate = "STANDYBY"
                time.sleep(10)
                continue
            elif currentstate == "STANDYBY":
                currentstate = "CONNECTED"

            # Veryify the connection to esp32 is working
            if currentstate == "CONNECTED":
                if phisical_conenction_update():
                    currentstate = "READY"
            

            # Start up the overlay and any other tasks before enterting the primary loop
            if currentstate == "READY":
                #run_gui(data_queue, stop_event) needs to be re-implemented
                currentstate = "RUNNING"
            
            # Primary loop handling overlay and feeding esp32 IMU data.
            if currentstate == "RUNNING":
                #PLACEHOLDER
                # Not currently implmented.
                print("PLACEHOLDER")


            #Check for crash amount
            if crashamount > 5:
                print("Overlay has crashed 5 times. Something is wrong. Exiting")
                break




        except KeyboardInterrupt:
            print("\nKeyboardInterrupt detected. Exiting")
            currentstate = "EXIT"
            break
        
        except Exception as e:
            if crashamount > 5:
                print("Overlay has crashed 5 times. Something is wrong.Exiting")
                break

            crashamount += 1
            print("Error something fucked up. error:", e)
            print(f"Restarting in 20 seconds to hopefully let it recover, crash amount: {crashamount}")
            time.sleep(20)

    if crashamount > 5 or currentstate == "EXIT":
        print("Overlay shutting down.")
        break

