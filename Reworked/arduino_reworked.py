import socket

import serial
import time
import enum
import GamepadController

class PedalState(enum.Enum):
    NEUTRAL = 0
    ACCEL = 1
    BRAKE = 2
    SKID = 3


class ArduinoReworked:

    def __init__(self, gamepad_controller : GamepadController):
        self.current_state = PedalState.NEUTRAL

        self.gc = gamepad_controller

        self.pedal_threshold = 3  # TODO Change this

    def process_pedal_data(self, is_accel_pressed, is_brake_pressed):
        # If both pedal are pressed, we skid

        if is_accel_pressed and is_brake_pressed and self.current_state != PedalState.SKID:
            if self.current_state == PedalState.BRAKE:
                self.gc.send_command("R_DOWN")

            self.current_state = PedalState.SKID

            self.gc.send_command("P_SKIDDING")

        elif is_accel_pressed and not is_brake_pressed and self.current_state != PedalState.ACCEL:
            self.release_state()
            self.current_state = PedalState.ACCEL
            # print("Accelerate")
            self.gc.send_command("P_UP")

        elif not is_accel_pressed and is_brake_pressed and self.current_state != PedalState.BRAKE:
            self.release_state()
            self.current_state = PedalState.BRAKE
            # print("Brake")
            self.gc.send_command("P_DOWN")

        elif not is_accel_pressed and not is_brake_pressed and self.current_state != PedalState.NEUTRAL:
            if self.current_state == PedalState.ACCEL:
                self.gc.send_command("R_UP")
                self.current_state = PedalState.NEUTRAL
            elif self.current_state == PedalState.BRAKE:
                self.gc.send_command("R_DOWN")
                self.current_state = PedalState.NEUTRAL
            elif self.current_state == PedalState.SKID:
                self.gc.send_command("R_SKIDDING")
                self.gc.send_command("R_UP")
                self.current_state = PedalState.NEUTRAL
            print("Neutral")

    def release_state(self):

        if self.current_state == PedalState.ACCEL:
            self.gc.send_command("R_UP")
        elif self.current_state == PedalState.BRAKE:
            self.gc.send_command("R_DOWN")
        elif self.current_state == PedalState.SKID:
            self.gc.send_command("R_SKIDDING")

    def read_ultrasound_data(self, port, baud_rate=9600):

        print("Arduino started")

        try:
            # Ouverture de la connexion série
            with serial.Serial(port, baud_rate, timeout=1) as ser:
                print(f"Connexion établie sur le port {port} avec un débit de {baud_rate} bauds.")

                while True:
                    # Lecture des données envoyées par l'Arduino
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8').strip()
                        if '#' in line:
                            # Séparer les données des deux capteurs
                            accel_data, brake_data = line.split('#')
                            # print(f"Distance de l'accélérateur: {accel_data} cm")
                            # print(f"Distance du frein: {brake_data} cm")

                            # If the data is less than the threshold, we consider the pedal is pressed

                            is_accel_pressed = int(accel_data) < self.pedal_threshold
                            is_brake_pressed = int(brake_data) < self.pedal_threshold

                            self.process_pedal_data(is_accel_pressed, is_brake_pressed)

                    time.sleep(0.1)

        except serial.SerialException as e:
            print(f"Erreur de connexion série : {e}")
        except KeyboardInterrupt:
            print("Arrêt du programme.")
