from arduino_ultrasound_reader import ArduinoUltrasoundReader


def main_arduino():

    server_address = 'localhost'  # TODO change this when running on different machines
    arduino_port = 6009

    arduino_ultrasound_reader = ArduinoUltrasoundReader(server_address, arduino_port)

    port = "COM3"
    arduino_ultrasound_reader.read_ultrasound_data(port)


if __name__ == '__main__':
    main_arduino()

