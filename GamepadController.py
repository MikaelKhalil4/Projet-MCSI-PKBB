
"""
This script aims to provide a class that will recieve input from differents scripts and trigger gamepag inputs.
"""
import time

import vgamepad



class GamepadController:
    def __init__(self, debug = False):
        self.debug = debug
        self.vg = vgamepad.VX360Gamepad()
        print("GamepadController initialized")

    def press_button(self, button, update = True):
        if self.debug:
            print("Button pressed : ", button)
        if button == "A":
            # Brake / Reverse
            self.vg.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_A)
        elif button == "B":
            # Accelerate
            self.vg.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_B)
        elif button == "X":
            # Rescue
            self.vg.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_X)
        elif button == "Y":
            # Look back
            self.vg.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_Y)
        elif button == "LB":
            # Nitro
            self.vg.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER )
        elif button == "RB":
            # Skid
            self.vg.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
        elif button == "LT":
            # Fire
            self.vg.left_trigger(255)
        elif button == "BACK":
            self.vg.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
        if update : self.vg.update()



    def release_button(self, button, update = True):
        if self.debug:
            print("Button released : ", button)
        if button == "A":
            self.vg.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_A)
        elif button == "B":
            self.vg.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_B)
        elif button == "X":
            self.vg.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_X)
        elif button == "Y":
            self.vg.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_Y)
        elif button == "LB":
            self.vg.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        elif button == "RB":
            self.vg.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
        elif button == "LT":
            self.vg.left_trigger(0)
        elif button == "BACK":
            self.vg.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_BACK)

        if update : self.vg.update()


    def signal(self):
        if self.debug:
            print("Signal")
        self.vg.press_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_START)
        self.vg.update()
        time.sleep(1)
        self.vg.release_button(vgamepad.XUSB_BUTTON.XUSB_GAMEPAD_START)
        self.vg.update()

    def steer(self, x):
        if self.debug:
            # print("Steer : ", x)
            pass
        # Used to steer
        self.vg.left_joystick_float(x, 0)
        self.vg.update()

