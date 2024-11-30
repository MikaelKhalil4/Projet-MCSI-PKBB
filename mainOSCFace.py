from osc_server import OSCServer
from time import sleep
from face_tracking import FaceTracking

"""
This file will be launched by the same Computer that will run the game and the STK_input_server.
He runs the OSCServer and the FaceTracking.
"""


def main_osc_face():

    server_address = 'localhost'
    osc_port = 6006
    face_port = 6010

    is_collab = False

    user_input = input("Which mode do you want to launch : 'c' for collaboration mode, 'p' for performance mode : ")

    while user_input not in ["c", "p"]:
        print("\nInvalid input! Please enter c or p.")
        user_input = input("Which mode do you want to launch : 'c' for collaboration mode, 'p' for performance mode : ")
    # Validate and convert input to a boolean
    if user_input == "c":
        is_collab = True
        tracker = FaceTracking(server_address, face_port)
        tracker.runtracking()

    elif user_input == "p":
        is_collab = False

    osc_server = OSCServer(is_collab, server_address, osc_port)

    try:
        sleep(1000)
    except KeyboardInterrupt:
        pass
    finally:
        osc_server.stop()


if __name__ == "__main__":
    main_osc_face()
