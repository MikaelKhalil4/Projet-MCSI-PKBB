

import threading

from Reworked.GamepadController import GamepadController
from Reworked.OSCServerReworked import OSCServerReworked
from Reworked.arduino_reworked import ArduinoReworked

if __name__ == "__main__":
    gamepadController = GamepadController()

    osc_server_reworked = OSCServerReworked(gamepadController, False)

    arduino_reworked = ArduinoReworked(gamepadController)

    port = "COM3"
    timer_arduino = threading.Timer(1, arduino_reworked.read_ultrasound_data, [port])
    timer_arduino.start()


    while True:
        inp = input("Press q to quit or any other key to map the gamepad")
        if inp == "q":
            break
        else:
            timer = threading.Timer(3, gamepadController.signal, [])
            timer.start()
            print("Signal sent")

    osc_server_reworked.osc.stop()