from controller import Controller
from osc_server import OSCServer
from time import sleep

def main():
    address = ('localhost', 6006)
    controller = Controller(address)
    osc_server = OSCServer(controller)
    osc_server.bind_callbacks()

    try:
        sleep(1000)
    except KeyboardInterrupt:
        pass
    finally:
        osc_server.stop()

if __name__ == "__main__":
    main()
