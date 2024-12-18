#!/usr/bin/env python3
#Michael ORTEGA - 09 jan 2018

###############################################################################
## Global libs
import sys
import socket
import keyboard
import threading

###############################################################################
## Global vars
GREEN       = '\033[92m'
WHITE       = '\x1b[0m'
BLUE        = '\033[94m'
YELLOW      = '\033[93m'
RED         = '\033[91m'

stop        = False
DEBUG       = True

address1    = ('0.0.0.0', 6006) # Port used for OSC Controller
address2    = ('0.0.0.0', 6007) # Port used by the QR Code Detection
address3    = ('0.0.0.0', 6008) # Port used by the Voice Action
address4    = ('0.0.0.0', 6009) # Port used by arduino
address5    = ('0.0.0.0', 60010) # Port used by Face Tracking


sock1       = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock1.bind(address1)

sock2       = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock2.bind(address2)

sock3       = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock3.bind(address3)

sock4       = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock4.bind(address4)

sock5       = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock5.bind(address5)

#list of tuples: (received command, keyboard key, keyboard func )
bindings    = [ ['UP', 'up', keyboard.press_and_release],
                ['DOWN', 'down', keyboard.press_and_release],
                ['LEFT', 'left', keyboard.press_and_release],
                ['RIGHT', 'right', keyboard.press_and_release],
                ['SELECT', 'enter', keyboard.press_and_release],
                ['CANCEL', 'backspace', keyboard.press_and_release],
                ['BACK', 'backspace', keyboard.press_and_release],
                ['FIRE', 'space', keyboard.press_and_release],
                ['P_FIRE', 'space', keyboard.press],
                ['R_FIRE', 'space', keyboard.release],
                ['NITRO', 'n', keyboard.press_and_release],
                ['P_NITRO', 'n', keyboard.press],
                ['R_NITRO', 'n', keyboard.release],
                ['P_SKIDDING', 'v', keyboard.press],
                ['R_SKIDDING', 'v', keyboard.release],
                ['P_LOOKBACK', 'b', keyboard.press],
                ['R_LOOKBACK', 'b', keyboard.release],
                ['RESCUE', 'backspace', keyboard.press_and_release],
                ['P_RESCUE', 'backspace', keyboard.press],
                ['R_RESCUE', 'backspace', keyboard.release],
                ['PAUSE', 'escape', keyboard.press_and_release],
                ['P_UP', 'up', keyboard.press],
                ['R_UP', 'up', keyboard.release],
                ['P_DOWN', 'down', keyboard.press],
                ['R_DOWN', 'down', keyboard.release],
                ['P_LEFT', 'left', keyboard.press],
                ['R_LEFT', 'left', keyboard.release],
                ['P_RIGHT', 'right', keyboard.press],
                ['R_RIGHT', 'right', keyboard.release],
                ['P_ACCELERATE', 'up', keyboard.press],
                ['R_ACCELERATE', 'up', keyboard.release],
                ['P_BRAKE', 'down', keyboard.press],
                ['R_BRAKE', 'down', keyboard.release],
                ]

commands = [b[0] for b in bindings]

###############################################################################
## Main
def handle_socket(sock):
    global stop
    while not stop:
        data, addr = sock.recvfrom(1024)
        if type(data) is bytes:
            data = data.decode("utf-8").replace(',', '')

        if data == 'STOPSERVEUR':
            stop = True
        else:
            if data in commands:
                if DEBUG: print(YELLOW + '\t' + data + WHITE)
                b = bindings[commands.index(data)]
                b[2](b[1])
            else:
                if DEBUG: print(RED + '\t' + data + WHITE + ' (Unknown)')

###############################################################################
## Main
if len(sys.argv) > 1:
    # Reading command line
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-d':
            DEBUG = True

print()
print('STK input server started ', end='')
if DEBUG:
    print(GREEN + '(Debug mode)' + WHITE)
else:
    print()

# Create threads to handle each socket
thread1 = threading.Thread(target=handle_socket, args=(sock1,))
thread2 = threading.Thread(target=handle_socket, args=(sock2,))
thread3 = threading.Thread(target=handle_socket, args=(sock3,))
thread4 = threading.Thread(target=handle_socket, args=(sock4,))
thread5 = threading.Thread(target=handle_socket, args=(sock5,))

thread1.start()
thread2.start()
thread3.start()
thread4.start()
thread5.start()

thread1.join()
thread2.join()
thread3.join()
thread4.join()
thread5.join()

print('STK input server stopped')
