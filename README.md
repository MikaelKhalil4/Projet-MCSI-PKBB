# OSC Controller Project ReadMe

## Overview

The project consists of three main parts:

- `Controller`: Handles the data received from the OSC server and sends commands to control the game.
- `OSCServer`: Receives OSC messages from a client and forwards them to the appropriate `Controller` methods. - In this file , inside the method bind_callbacks we have multiple blocks commented for each section of the tp, so in order to test each part, just remove the comments

- `main`: Initializes the `Controller` and the `OSCServer`, and starts the server.

In order to run the script, just run the mainTP1.py and STK_input_server and it will work!

The files regarding the TP1 are:

- mainTP1.py , steering_acceleration.py , controller.py and osc_server.py .
  and for the TP2:
- face_tracking.py and handtracking.cs .
