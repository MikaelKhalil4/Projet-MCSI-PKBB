import threading

from Reworked.GamepadController import GamepadController
from Reworked.OSCServerReworked import OSCServerReworked
from Reworked.QrCodeReworked import QRDetectorReworked
from Reworked.voiceActionReworked import VoiceActionReworked

if __name__ == "__main__":
    gamepadController = GamepadController(True)

    osc_server_reworked = OSCServerReworked(gamepadController, False)

    qr_code_reworked = QRDetectorReworked(gamepadController)
    timer_qr = threading.Timer(1, qr_code_reworked.run, [])
    timer_qr.start()

    voice_action_reworked = VoiceActionReworked(gamepadController)
    timer_voice = threading.Timer(1, voice_action_reworked.run, [])
    timer_voice.start()


    while True:
        inp = input("Press q to quit or any other key to map the gamepad")
        if inp == "q":
            break
        else:
            timer = threading.Timer(3, gamepadController.signal, [])
            timer.start()
            print("Signal sent")

    osc_server_reworked.osc.stop()