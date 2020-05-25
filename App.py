import sys
import time

from PySide2 import QtCore, QtWidgets, QtGui
import pigpio

import cv2 as cv

'''
Created on May 21, 2020
@author: Evgenii_Lartcev

Notes:

- In early RC applications, the PWM signal min and max values were always between 1 and 2ms,
and the frequency was 50Hz (period of 20ms). 
A pulse of 1ms corresponds to zero throttle, and a pulse of 2ms to maximum throttle. 
In pigpio library: param 'pulsewidth': The servo pulsewidth in microseconds. 0 switches pulses off.

- if you get ImportError: /usr/lib/x86_64-linux-gnu/libQt5OpenGL.so.5: undefined symbol: _Z12qTriangulateRK11QVectorPathRK10QTransformd
that means you are using an OpenCV version built with your system's Qt 
while your PySide2 (or PyQt5) installation comes with it's own Qt dependencies and they are clashing 
because you are trying to load two different versions of Qt with the same namespace in the same memory space.
Either install opencv-python through pip or use your distribution provided PyQt5.
'''


class MainWidget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setFixedSize(800, 600)

        self.esc_gpio_pin = 25
        self.piHost = "192.168.0.98"  # make sure on RaspberryPi "sudo pigpiod" was being run
        print("Init connection to pigpio daemon on " + self.piHost)
        self.pi = pigpio.pi(self.piHost)  # no arguments or "localhost" if started on RaspberryPi
        if not self.pi.connected:
            print("Can't connect to " + self.piHost)
            exit()
        self.pi.set_servo_pulsewidth(self.esc_gpio_pin, 0)  # Starts (500-2500) or stops (0) servo pulses on the GPIO. We need to suppose that default frequency is 50 Hz.
        print("Connection to pigpio daemon on " + self.piHost + " established, drive set to stop.")

        # in microseconds - ESC control by using old analog PWM style
        self.maxPulseWidth = 2000
        self.minPulseWidth = 700

        self.escCalibrationButton = QtWidgets.QPushButton("Calibrate ESC")
        self.escCalibrationButton.clicked.connect(self.calibrate)

        self.escSpeedControlSlider = QtWidgets.QSlider()
        self.escSpeedControlSlider.setOrientation(QtCore.Qt.Vertical)
        self.escSpeedControlSlider.setMinimum(self.minPulseWidth)  # should be 0
        self.escSpeedControlSlider.setMaximum(self.maxPulseWidth)  # should be 100
        self.escSpeedControlSlider.valueChanged.connect(self.manageEscSpeed)

        self.driveFullyStopped = False
        self.escStopButton = QtWidgets.QPushButton("Stop drive forever.")
        self.escStopButton.setMinimumWidth(150)
        self.escStopButton.setStyleSheet("background-color: rgba(245, 65, 19, 1);")
        self.escStopButton.clicked.connect(self.stop_and_release)

        self.debugLog = QtWidgets.QTextEdit(
            "Connection to pigpio daemon on " + self.piHost + " established, drive set to stop.")
        self.debugLog.append("OpenCV version is " + cv.__version__)
        self.debugLog.setReadOnly(True)
        self.debugLog.setMaximumHeight(200)

        self.main_layout = QtWidgets.QHBoxLayout()

        self.esc_layout = QtWidgets.QVBoxLayout()
        self.esc_layout.addWidget(self.escSpeedControlSlider)
        self.esc_layout.addWidget(self.escCalibrationButton)
        self.esc_layout.addWidget(self.escStopButton)

        self.debug_layout = QtWidgets.QVBoxLayout()
        self.debug_layout.setAlignment(QtCore.Qt.AlignBottom)
        self.debug_layout.addWidget(self.debugLog)

        self.main_layout.addLayout(self.esc_layout)
        self.main_layout.addLayout(self.debug_layout)

        self.setLayout(self.main_layout)

    # This is the auto calibration procedure of a normal ESC
    def calibrate(self):
        if not self.driveFullyStopped:
            self.debugLog.append("Stopping drive...")
            self.pi.set_servo_pulsewidth(self.esc_gpio_pin, 0)
            print("Disconnect the battery and press Enter")
            inp = input()
            if inp == '':
                self.pi.set_servo_pulsewidth(self.esc_gpio_pin, self.maxPulseWidth)
                print("Connect the battery.. you will here two beeps, then wait for a gradual falling tone then press Enter")
                inp = input()
                if inp == '':
                    self.pi.set_servo_pulsewidth(self.esc_gpio_pin, self.minPulseWidth)
                    print("There should be a special tone")
                    time.sleep(12)
                    print("Please wait for it ....")
                    self.pi.set_servo_pulsewidth(self.esc_gpio_pin, 0)
                    time.sleep(2)
                    print("Arming ESC now...")
                    self.pi.set_servo_pulsewidth(self.esc_gpio_pin, self.minPulseWidth)
                    time.sleep(1)
                    print("ESC has been successfully calibrated.")
                    self.debugLog.append("ESC has been successfully calibrated. Use slider to run drive.")
        else:
            self.debugLog.append("ESC and drive has been fully stopped already. Restart available only with program.")

    # This will stop every action your Pi is performing for ESC or allow run for drive.
    def stop_and_release(self):
        if not self.driveFullyStopped:
            self.pi.set_servo_pulsewidth(self.esc_gpio_pin, 0)
            self.pi.stop()
            self.escStopButton.setText("ESC stopped.")
            self.debugLog.append("ESC and drive has been fully stopped. Restart available only with program.")
            self.driveFullyStopped = True
            self.escSpeedControlSlider.setValue(self.minPulseWidth)
        else:
            self.debugLog.append("ESC and drive has been fully stopped already. Restart available only with program.")

    def manageEscSpeed(self):
        # self.debugLog.setText(str(self.escSpeedControlSlider.value())) #debug only
        if not self.driveFullyStopped:
            self.pi.set_servo_pulsewidth(self.esc_gpio_pin, self.escSpeedControlSlider.value())
        else:
            self.debugLog.append("ESC has been fully stopped already.")
            self.escSpeedControlSlider.setValue(self.minPulseWidth)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = MainWidget()
    widget.show()
    sys.exit(app.exec_())
