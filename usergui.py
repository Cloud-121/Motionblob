import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QLabel, QPushButton, QMessageBox, QHBoxLayout,
    QGroupBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
import json
import os

# Location for files
CONFIG_FILE = 'config.json'
logo_path = 'logos/motionblob.png'

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

def backend_communication(ask):
    if ask == "connection_status":
        return True

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

        if backend_communication("connection_status"):
            backend_status = "Connected"
        else:
            backend_status = (f"Disconnected: {backend_status}")
        self.backend_status_label = QLabel(f"Backend Status: {backend_status}", self)
        self.backend_status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.backend_status_label)

        imu_settings_groupbox = QGroupBox("IMU Selection", self)
        imu_layout = QVBoxLayout()

        self.imu_type_display_label = QLabel(f'Current IMU: {self.current_imu_type}', self)
        self.imu_type_display_label.setAlignment(Qt.AlignCenter)
        imu_layout.addWidget(self.imu_type_display_label)

        self.phone_radio = QRadioButton("Phone", self)
        self.esp32_radio = QRadioButton("ESP32", self)

        self.imu_type_button_group = QButtonGroup(self)
        self.imu_type_button_group.addButton(self.phone_radio)
        self.imu_type_button_group.addButton(self.esp32_radio)

        self.phone_radio.toggled.connect(lambda checked: self.set_imu_type('Phone') if checked else None)
        self.esp32_radio.toggled.connect(lambda checked: self.set_imu_type('ESP32') if checked else None)

        if self.current_imu_type == 'Phone':
            self.phone_radio.setChecked(True)
        elif self.current_imu_type == 'ESP32':
            self.esp32_radio.setChecked(True)

        imu_layout.addWidget(self.phone_radio)
        imu_layout.addWidget(self.esp32_radio)

        imu_settings_groupbox.setLayout(imu_layout)
        main_layout.addWidget(imu_settings_groupbox)

        main_layout.addStretch(1)

        self.bottom_header_label = QLabel("Made with ❤️ by <a href=\"https://github.com/Cloud-121\">Cloud-121</a>", self)
        self.bottom_header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.bottom_header_label)

        self.setLayout(main_layout)

    def set_imu_type(self, imu_type):
        if self.current_imu_type == imu_type:
            return

        self.current_imu_type = imu_type
        if imu_type == 'Phone':
            print("Phone IMU selected")
            write_config('IMU_TYPE', 'Phone')
        elif imu_type == 'ESP32':
            print("ESP32 IMU selected")
            write_config('IMU_TYPE', 'ESP32')

        self.imu_type_display_label.setText(f'Current IMU: {self.current_imu_type}')


app = QApplication(sys.argv)
main_window = Frontendbase()
main_window.show()
sys.exit(app.exec_())