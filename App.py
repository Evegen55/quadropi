import sys
import time

from PySide2 import QtCore, QtWidgets, QtGui
import pigpio

'''
 In early RC applications, the PWM signal min and max values were always between 1 and 2ms,
and the frequency was 50Hz (period of 20ms). 
a pulse of 1ms corresponds to zero throttle, and a pulse of 2ms to maximum throttle. 
in pigpio library: param 'pulsewidth': The servo pulsewidth in microseconds. 0 switches pulses off.
'''


class MainWidget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setFixedSize(800, 600)

        print("Init connection to pigpio daemon")
        self.esc_gpio_pin = 25
        self.piHost = "192.168.0.98"  # make sure on RaspberryPi "sudo pigpiod" was being run
        print("Init connection to pigpio daemon on " + self.piHost)
        self.pi = pigpio.pi(self.piHost)  # no arguments or "localhost" if started on RaspberryPi
        if not self.pi.connected:
            print("Can't connect to " + self.piHost)
            exit()
        self.pi.set_servo_pulsewidth(self.esc_gpio_pin, 0)  # Starts (500-2500) or stops (0) servo pulses on the GPIO. We need to suppose that default frequency is 50 Hz.

        # in microseconds - ESC control by using old analog PWM style
        self.maxPulseWidth = 2000
        self.minPulseWidth = 700

        self.escCalibrationButton = QtWidgets.QPushButton("Calibrate ESC")
        # self.escCalibrationButton.adjustSize()
        self.escCalibrationButton.clicked.connect(self.calibrate)

        self.escStopButton = QtWidgets.QPushButton("Stop drive and ESC.")
        # self.escStopButton.adjustSize()
        self.escStopButton.clicked.connect(self.stop)
        self.driveStopped = False

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
        if self.driveStopped:
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
                    self.debugLog.setText("ESC has been successfully calibrated. Restart program to run drive.")
        else:
            self.debugLog.setText("Please stop the drive motion.")

    # This will stop every action your Pi is performing for ESC or allow run for drive.
    def stop(self):
        if not self.driveStopped:
            self.pi.set_servo_pulsewidth(self.esc_gpio_pin, 0)
            self.pi.stop()
            self.escStopButton.setText("ESC has been fully stopped.")
            self.driveStopped = True
        else:
            self.escStopButton.setText("ESC has been fully stopped already.")


    def manageEscSpeed(self):
        # self.debugLog.setText(str(self.escSpeedControlSlider.value())) #debug only
        if not self.driveStopped:
            self.pi.set_servo_pulsewidth(self.esc_gpio_pin, self.escSpeedControlSlider.value())
        else:
            self.escStopButton.setText("ESC has been fully stopped already.")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = MainWidget()
    widget.show()
    sys.exit(app.exec_())
