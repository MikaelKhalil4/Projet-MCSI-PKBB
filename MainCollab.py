import threading
from time import sleep

from GamepadController import GamepadController
from OSCServerReworked import OSCServerReworked

if __name__ == "__main__":
    gamepadController = GamepadController()
    osc_server_reworked = OSCServerReworked(gamepadController, False)

    while True:
        inp = input("Press q to quit or any other key to map the gamepad")
        if inp == "q":
            break
        else:
            timer = threading.Timer(3, gamepadController.signal, [])
            timer.start()
            print("Signal sent")

    osc_server_reworked.osc.stop()