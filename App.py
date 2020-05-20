import sys
import time

from PySide2 import QtCore, QtWidgets, QtGui
import pigpio


class MainWidget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setFixedSize(800, 600)

        self.esc_gpio_pin = 25
        self.piHost = "192.168.0.98" # make sure on RaspberryPi "sudo pigpiod" was being run
        self.pi = pigpio.pi(self.piHost) # no arguments if started on RaspberryPi
        self.pi.set_servo_pulsewidth(self.esc_gpio_pin, 0)

        # in microseconds - ESC control by using old analog PWM style
        self.maxPulseWidth = 2000
        self.minPulseWidth = 700

        self.escCalibrationButton = QtWidgets.QPushButton("Calibrate ESC")
        self.escCalibrationButton.clicked.connect(self.calibrate)

        self.escStopButton = QtWidgets.QPushButton("Stop")
        self.escStopButton.clicked.connect(self.stop)

        self.escSpeedControlSlider = QtWidgets.QSlider()
        self.escSpeedControlSlider.setOrientation(QtCore.Qt.Vertical)
        self.escSpeedControlSlider.setMinimum(self.minPulseWidth) # should be 0
        self.escSpeedControlSlider.setMaximum(self.maxPulseWidth) # should be 100
        self.escSpeedControlSlider.valueChanged.connect(self.manageEscSpeed)

        self.debugLog = QtWidgets.QLabel("Hello!")
        self.debugLog.setAlignment(QtCore.Qt.AlignRight)

        self.main_layout = QtWidgets.QHBoxLayout()

        self.esc_layout = QtWidgets.QVBoxLayout()
        # self.esc_layout.setAlignment(QtCore.Qt.AlignHCenter)
        self.esc_layout.addWidget(self.escSpeedControlSlider)
        self.esc_layout.addWidget(self.escStopButton)
        self.esc_layout.addWidget(self.escCalibrationButton)

        self.debug_layout = QtWidgets.QVBoxLayout()
        self.debug_layout.addWidget(self.debugLog)

        self.main_layout.addLayout(self.esc_layout)
        self.main_layout.addLayout(self.debug_layout)

        self.setLayout(self.main_layout)

    # This is the auto calibration procedure of a normal ESC
    def calibrate(self):
        self.pi.set_servo_pulsewidth(self.esc_gpio_pin, 0)
        self.debugLog.setText("Disconnect the battery and press Enter")
        inp = input()
        if inp == '':
            self.pi.set_servo_pulsewidth(self.esc_gpio_pin, self.maxPulseWidth)
            self.debugLog.setText("Connect the battery.. you will here two beeps, then wait for a gradual falling tone then press Enter")
            inp = input()
            if inp == '':
                self.pi.set_servo_pulsewidth(self.esc_gpio_pin, self.minPulseWidth)
                self.debugLog.setText("There should be a special tone")
                time.sleep(12)
                self.debugLog.setText("Please wait for it ....")
                self.pi.set_servo_pulsewidth(self.esc_gpio_pin, 0)
                time.sleep(2)
                self.debugLog.setText("Arming ESC now...")
                self.pi.set_servo_pulsewidth(self.esc_gpio_pin, self.minPulseWidth)
                time.sleep(1)
                self.debugLog.setText("ESC has been successfully calibrated.")

    # This will stop every action your Pi is performing for ESC.
    def stop(self):
        self.pi.set_servo_pulsewidth(self.esc_gpio_pin, 0)
        self.pi.stop()

    def manageEscSpeed(self):
        # self.debugLog.setText(str(self.escSpeedControlSlider.value())) #debug only
        self.pi.set_servo_pulsewidth(self.esc_gpio_pin, self.escSpeedControlSlider.value())


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = MainWidget()
    widget.show()
    sys.exit(app.exec_())
