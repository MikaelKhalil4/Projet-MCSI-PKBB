import socket

import serial
import time
import enum


class PedalState(enum.Enum):
    NEUTRAL = 0
    ACCEL = 1
    BRAKE = 2
    SKID = 3


class ArduinoUltrasoundReader:

    def __init__(self, _server_address='localhost', _arduino_port=6009):
        self.server_address = (_server_address, _arduino_port)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.current_state = PedalState.NEUTRAL

        self.pedal_threshold = 10  # TODO Change this

    def process_pedal_data(self, is_accel_pressed, is_brake_pressed):
        # If both pedal are pressed, we skid

        data = b""

        if is_accel_pressed and is_brake_pressed and self.current_state != PedalState.SKID:
            if self.current_state == PedalState.BRAKE:
                data = b'R_DOWN'
                self.send_data(data)

            self.current_state = PedalState.SKID
            print("Skid")
            data = b'P_SKIDDING'

        elif is_accel_pressed and not is_brake_pressed and self.current_state != PedalState.ACCEL:
            self.release_state()
            self.current_state = PedalState.ACCEL
            print("Accelerate")
            data = b'P_UP'

        elif not is_accel_pressed and is_brake_pressed and self.current_state != PedalState.BRAKE:
            self.release_state()
            self.current_state = PedalState.BRAKE
            print("Brake")
            data = b'P_DOWN'

        elif not is_accel_pressed and not is_brake_pressed and self.current_state != PedalState.NEUTRAL:
            if self.current_state == PedalState.ACCEL:
                data = b'R_UP'
                self.current_state = PedalState.NEUTRAL
            elif self.current_state == PedalState.BRAKE:
                data = b'R_DOWN'
                self.current_state = PedalState.NEUTRAL
            elif self.current_state == PedalState.SKID:
                data = b'R_SKIDDING'
                self.send_data(data)
                data = b"R_UP"
                self.current_state = PedalState.NEUTRAL
            print("Neutral")

        self.send_data(data)

    def release_state(self):
        data = b""
        if self.current_state == PedalState.ACCEL:
            data = b'R_UP'
        elif self.current_state == PedalState.BRAKE:
            data = b'R_DOWN'
        elif self.current_state == PedalState.SKID:
            data = b'R_SKIDDING'
        self.send_data(data)

    def send_data(self, data):
        if len(data) > 0:
            self.client_socket.sendto(data, self.server_address)

    def read_ultrasound_data(self, port, baud_rate=9600):

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
