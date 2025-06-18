import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QLabel, QPushButton, QMessageBox, QHBoxLayout,
    QGroupBox, QRadioButton, QButtonGroup, QLineEdit
)
# 1. IMPORT QTIMER
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
import json
import requests
import os

# Location for files
CONFIG_FILE = 'config.json'
logo_path = 'logos/motionblob.png'
socketport = 1202

# Functions for reading config

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

#Gen Functions

def backend_communication(command):
    if command == "connection_status":
        try:
            if requests.get(f"http://127.0.0.1:{socketport}/status", timeout=1).status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            return False
        except requests.exceptions.Timeout:
            return False
    elif command == "update_config":
        try:
            requests.post(f"http://127.0.0.1:{socketport}/refreshconfig")
            return True
        except:
            return False
    elif command == "state":
        try:
            return requests.get(f"http://127.0.0.1:{socketport}/status").json()["status"]
        except:
            return "Unknown"

#frontend
class Frontendbase(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Motion Blob Settings')
        self.setGeometry(100, 100, 400, 500)
        self.current_imu_type = read_config('IMU_TYPE')
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.logo_label = QLabel(self)
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaledToWidth(150, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
            self.logo_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self.logo_label)
        else:
            self.logo_label.setText("Logo not found: 'logos/motionblob.png'")
            self.logo_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self.logo_label)
            print(f"Error: Logo file not found at '{logo_path}'. Please ensure the path is correct and the file exists.")

        self.backend_status_label = QLabel("Backend Status: Checking...", self)
        self.backend_status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.backend_status_label)

        self.backend_state_label = QLabel(" ", self)
        self.backend_state_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.backend_state_label)

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_connection_status)
        self.status_timer.start(6000)

        self.update_connection_status()

        imu_settings_groupbox = QGroupBox("IMU Selection", self)
        imu_layout = QVBoxLayout()

        self.imu_type_display_label = QLabel(f'Current IMU: {self.current_imu_type}', self)
        self.imu_type_display_label.setAlignment(Qt.AlignCenter)
        imu_layout.addWidget(self.imu_type_display_label)

        phone_layout = QHBoxLayout()

        self.phone_radio = QRadioButton("Phone", self)

        self.phone_ip_input = QLineEdit(self)
        self.phone_ip_input.setPlaceholderText("Enter Phone IP")

        self.phone_ip_input.setText(read_config("PHONE_IP") or "") 

        self.phone_ip_input.editingFinished.connect(self.save_phone_ip)
        

        phone_layout.addWidget(self.phone_radio)
        phone_layout.addWidget(self.phone_ip_input)
        
        self.esp32_radio = QRadioButton("ESP32", self)
        

        imu_layout.addLayout(phone_layout)

        imu_layout.addWidget(self.esp32_radio)
        

        self.imu_type_button_group = QButtonGroup(self)
        self.imu_type_button_group.addButton(self.phone_radio)
        self.imu_type_button_group.addButton(self.esp32_radio)

        self.phone_radio.toggled.connect(lambda checked: self.set_imu_type('Phone') if checked else None)
        self.esp32_radio.toggled.connect(lambda checked: self.set_imu_type('ESP32') if checked else None)

        if self.current_imu_type == 'Phone':
            self.phone_radio.setChecked(True)
            self.phone_ip_input.setEnabled(True)
        elif self.current_imu_type == 'ESP32':
            self.esp32_radio.setChecked(True)
            self.phone_ip_input.setEnabled(False)
        else:
            self.phone_ip_input.setEnabled(False)

        imu_settings_groupbox.setLayout(imu_layout)
        main_layout.addWidget(imu_settings_groupbox)

        main_layout.addStretch(1)

        self.bottom_header_label = QLabel("Made with ❤️ by <a href=\"https://github.com/Cloud-121\">Cloud-121</a>", self)
        self.bottom_header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.bottom_header_label)

        self.setLayout(main_layout)

    def update_connection_status(self):
        """Checks the backend connection and updates the status label."""
        if backend_communication("connection_status"):
            backend_status = "Connected"
            self.backend_status_label.setStyleSheet("color: green;")
            self.backend_state_label.setText(f"State: {backend_communication('state')}")
        else:
            backend_status = "Disconnected"
            self.backend_status_label.setStyleSheet("color: red;")
            self.backend_state_label.setText("")
        self.backend_status_label.setText(f"Backend Status: {backend_status}")

---
    def save_phone_ip(self):
        """Saves the content of the phone IP input field to the config."""
        ip_address = self.phone_ip_input.text()
        print(f"Saving Phone IP: {ip_address}")
        write_config('PHONE_IP', ip_address)
        # Notify the backend that the config has changed
        backend_communication("update_config")

    def set_imu_type(self, imu_type):
        if self.current_imu_type == imu_type:
            return

        self.current_imu_type = imu_type
        if imu_type == 'Phone':
            print("Phone IMU selected")
            write_config('IMU_TYPE', 'Phone')
            self.phone_ip_input.setEnabled(True)
            backend_communication("update_config")

        elif imu_type == 'ESP32':
            print("ESP32 IMU selected")
            write_config('IMU_TYPE', 'ESP32')
            self.phone_ip_input.setEnabled(False)
            backend_communication("update_config")

        self.imu_type_display_label.setText(f'Current IMU: {self.current_imu_type}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = Frontendbase()
    main_window.show()
    sys.exit(app.exec_())