from controller import Controller
from osc_server import OSCServer
from time import sleep

def main():
    osc_server = OSCServer()
    #here should start all everything like face tracking etc


    try:
        sleep(1000)
    except KeyboardInterrupt:
        pass
    finally:
        osc_server.stop()

if __name__ == "__main__":
    main()
