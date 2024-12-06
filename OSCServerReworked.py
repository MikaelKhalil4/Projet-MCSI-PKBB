from oscpy.server import OSCThreadServer
import socket
import threading
import time

from GamepadController import GamepadController


class OSCServerReworked:

    def __init__(self, gamepad_controller: GamepadController, is_collab: bool):
        self.gc = gamepad_controller

        self.osc = OSCThreadServer(default_handler=self.dump)
        self.sock = self.osc.listen(address='0.0.0.0', port=8000,
                                    default=True)

        if is_collab:
            self.bind_callbacks_collab()
        else:
            self.bind_callbacks_perf()

        self.is_right_pressed = False
        self.is_left_pressed = False
        self.time_right_first_pressed = 0
        self.time_left_first_pressed = 0
        self.is_right_double_tap = False
        self.is_left_double_tap = False
        self.actionned = False

        self.last_rescue_time = 0
        self.previous_y_accel = None
        self.accel_buffer = []

        print("OSC Server started")

    def bind_callbacks_collab(self):
        self.osc.bind(b'/multisense/orientation/roll', self.callback_roll_right_left)
        self.osc.bind(b'/multisense/orientation/pitch', self.callback_pitch_acc)

    def bind_callbacks_perf(self):
        self.osc.bind(b'/multisense/orientation/yaw', self.callback_yaw_right_left)
        self.osc.bind(b'/multisense/pad/x', self.callback_x_touchpad)
        self.osc.bind(b'/multisense/pad/touchUP', self.callback_touchup)
        self.osc.bind(b'/multisense/accelerometer/y', self.callback_acceleration_shaker_rescue)

    def dump(self, address, *values):
        """Default handler for unbound OSC messages."""
        """print(u'{}: {}'.format(
            address.decode('utf8'),
            ', '.join(
                '{}'.format(
                    v.decode('utf8') if isinstance(v, bytes) else v
                )
                for v in values if values
            )
        ))"""

    def callback_roll_right_left(self, *values):
        # Used in  collab to turn right or left
        roll = values[0]

        # Angle at which the steer is at its maximum
        max_angle = 30

        # Clamp the roll value to -max_angle, max_angle
        roll = max(min(roll, max_angle), -max_angle)

        # Map the roll value to -1,1
        roll = roll / max_angle

        self.gc.steer(roll)

    def callback_pitch_acc(self, *values):
        # Used in collab to accelerate
        pitch = values[0]

        # If angle is less than a value, we accelerate

        Accel_angle = -5

        if pitch < Accel_angle:
            self.gc.press_button("A")
        else:
            self.gc.release_button("A")

    def callback_yaw_right_left(self, *values):
        # Used in perf to turn right or left
        yaw = values[0]

        # Angle at which the steer is at its maximum
        max_angle = 20

        # Clamp the yaw value to -max_angle, max_angle
        yaw = max(min(yaw, max_angle), -max_angle)

        # Map the yaw value to -1,1
        yaw = - yaw / max_angle

        self.gc.steer(yaw)

    def callback_x_touchpad(self, *values):
        # Used in perf to : Fire, Skid, Nitro and rescue
        # We can only get a single point on the touchPad
        # On the right of the screen :
        #   - Simple tap + hold : Nitro
        #   - Double tap + hold :
        # On the left of the screen :
        #   - Simple tap : Fire
        #   - Double tap : Rescue

        if self.actionned:
            return

        time_to_double_tap_right = 0.2
        time_to_double_tap_left = 0.2

        x = values[0]

        if x < 0:
            # We pressed right

            if not self.is_right_pressed:
                # First frame we clicked right
                # We check if we double tapped
                if time.time() - self.time_right_first_pressed < time_to_double_tap_right:
                    # We double tapped
                    # print("Double tap right")
                    self.actionned = True
                    self.gc.press_button("RB")

                else:
                    # We pressed right, we have to wait until we are sure it's not a double tap
                    # print("First Press")
                    self.time_right_first_pressed = time.time()
            else:
                # Check if it has been pressed for long enough to say it's not a double tap
                if time.time() - self.time_right_first_pressed > time_to_double_tap_right:
                    # print("Time since first press : ", time.time() - self.time_first_pressed)
                    # print("Simple Tap right")
                    # We have simple pressed and hold right, we trigger the nitro
                    self.actionned = True
                    self.gc.press_button("LB")

            self.is_right_pressed = True

        else:
            # We pressed left

            if not self.is_left_pressed:
                # First frame we clicked right
                # We check if we double tapped
                if time.time() - self.time_left_first_pressed < time_to_double_tap_left:
                    # We double tapped so we look back
                    # print("Double tap left")
                    self.actionned = True
                    self.gc.press_button("Y")

                else:
                    # We pressed left, we have to wait until we are sure it's not a double tap
                    # print("First Press")
                    self.time_left_first_pressed = time.time()
            else:
                # Check if it has been pressed for long enough to say it's not a double tap
                if time.time() - self.time_left_first_pressed > time_to_double_tap_left:
                    # print("Time since first press : ", time.time() - self.time_first_pressed)
                    # print("Simple Tap left")
                    # We have simple pressed right so we fire
                    self.actionned = True
                    self.gc.press_button("B")

            self.is_left_pressed = True

    def callback_touchup(self, *values):
        # Release every button when we release the touchpad
        self.gc.release_button("LB", False)
        self.gc.release_button("RB", False)
        self.gc.release_button("B", False)
        self.gc.release_button("BACK", True)
        self.actionned = False
        self.is_right_pressed = False
        self.is_left_pressed = False

    def callback_acceleration_shaker_rescue(self, *values):
        """Handle acceleration from the smartphone to detect shakes and send rescue command."""
        DERIVATIVE_THRESHOLD = 3  # The amount of acceleration change required to detect a shake
        SHAKE_DURATION = 1.0  # Time window to detect shakes

        LAST_RESCUE_TIME = 1.0  # Minimum time between rescue commands

        y_accel = values[0]

        if self.previous_y_accel is not None:
            # Calculate the change (derivative) in acceleration
            accel_derivative = abs(y_accel - self.previous_y_accel)
        else:
            accel_derivative = 0.0

        self.previous_y_accel = y_accel

        current_time = time.time()

        # Add current derivative and timestamp to the buffer
        self.accel_buffer.append((current_time, accel_derivative))

        # Remove old values beyond the shake duration
        self.accel_buffer = [(t, d) for t, d in self.accel_buffer if t >= current_time - SHAKE_DURATION]

        # print("Accel : ",str(len(self.accel_buffer))," ",str([round(a,3) for _, a in self.accel_buffer]))
        # Check for consistent shaking (mean value above the threshold)

        mean_derivative = sum(a for _, a in self.accel_buffer) / len(self.accel_buffer)

        if len(self.accel_buffer) >= 50 and mean_derivative > DERIVATIVE_THRESHOLD:
            # Check if last rescue command was sent more than LAST_RESCUE_TIME
            if current_time - self.last_rescue_time > LAST_RESCUE_TIME:
                self.last_rescue_time = current_time
                print("Shake detected!")
                self.gc.press_button("Y")

    def stop(self):
        self.osc.close()
