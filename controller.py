import socket
import threading
from steering_acceleration import STEER, ACCEL
import time
import math
last_tap_time = 0
DOUBLE_TAP_THRESHOLD = 0.5  # Time in seconds between taps to consider it a double tap
STEER_THRES = 0.4
ACCEL_THRES = 0.4
STEER_ANGLE_THRES = 20
ACCEL_ANGLE_THRES = 15
ACCEL_ANGLE_OFFSET = -50
class Controller:

    def __init__(self, address):
        self.current_steering = STEER.NEUTRAL
        self.current_accel = ACCEL.NEUTRAL
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = address
        self.last_tap_time = 0
        self.tap_count = 0
        self.shake_threshold = 10  # Adjust this value as needed
        self.shake_window = 1.0  # Time window to detect shakes
        self.shake_count_threshold = 3  # Number of shakes required
        self.accel_history = []
        self.last_shake_time = 0
        self.previous_yaw=0.0
        
        
        self.steering_value = 0.0  # Continuous value between 0 and 1 for steering
        self.steering_direction = STEER.NEUTRAL  # Current steering direction

        self.accel_value = 0.0  # Continuous value between 0 and 1 for acceleration
        self.accel_direction = ACCEL.NEUTRAL  # Current acceleration direction

        # Control loop variables
        self.loop_running = True
        self.control_thread = threading.Thread(target=self.control_loop)
        self.control_thread.start()


    def send_data(self, data):
        if len(data) > 0:
            self.client_socket.sendto(data, self.address)


    def callback_x_continuous(self, *values):
        print("got values for x: {}".format(values))
        data = b''
        acceleration = ACCEL.NEUTRAL

        if values[0] < -STEER_THRES:
            acceleration = ACCEL.DOWN
        elif values[0] > STEER_THRES:
            acceleration = ACCEL.UP

        if self.current_accel != ACCEL.NEUTRAL and acceleration == ACCEL.NEUTRAL:
            if self.current_accel == ACCEL.UP:
                data = b'R_UP'
            elif self.current_accel == ACCEL.DOWN:
                data = b'R_DOWN'

        if self.current_accel == ACCEL.NEUTRAL and acceleration != ACCEL.NEUTRAL:
            if acceleration == ACCEL.UP:
                data = b'P_UP'
            elif acceleration == ACCEL.DOWN:
                data = b'P_DOWN'

        self.send_data(data)
        self.current_accel = acceleration

    def callback_y_continuous(self, *values):
        print("got values for y: {}".format(values))
        data = b''
        steering = STEER.NEUTRAL

        if values[0] < -ACCEL_THRES:
            steering = STEER.LEFT
        elif values[0] > ACCEL_THRES:
            steering = STEER.RIGHT

        if self.current_steering != STEER.NEUTRAL and steering == STEER.NEUTRAL:
            if self.current_steering == STEER.LEFT:
                data = b'R_LEFT'
            elif self.current_steering == STEER.RIGHT:
                data = b'R_RIGHT'

        if self.current_steering == STEER.NEUTRAL and steering != STEER.NEUTRAL:
            if steering == STEER.LEFT:
                data = b'P_LEFT'
            elif steering == STEER.RIGHT:
                data = b'P_RIGHT'

        self.send_data(data)
        self.current_steering = steering

    def callback_touchUP_continuous(self, *values):
        
        data = b''

        if self.current_accel != ACCEL.NEUTRAL:
            if self.current_accel == ACCEL.UP:
                data = b'R_UP'
            elif self.current_accel == ACCEL.DOWN:
                data = b'R_DOWN'
        
        if self.current_steering != STEER.NEUTRAL:
            if self.current_steering == STEER.LEFT:
                data = b'R_LEFT'
            elif self.current_steering == STEER.RIGHT:
                data = b'R_RIGHT'

        self.send_data(data)
     
     
     
        
    def process_steering(self,steering):
        
        

        data = b''

        if self.current_steering != STEER.NEUTRAL and steering == STEER.NEUTRAL:
            if self.current_steering == STEER.LEFT:
                data = b'R_LEFT'
            elif self.current_steering == STEER.RIGHT:
                data = b'R_RIGHT'

        if self.current_steering == STEER.NEUTRAL and steering != STEER.NEUTRAL:
            if steering == STEER.LEFT:
                data = b'P_LEFT'
            elif steering == STEER.RIGHT:
                data = b'P_RIGHT'

        if len(data) > 0:
            self.send_data(data)

        self.current_steering = steering

    def process_acceleration(self,acceleration):
        data = b''

        

        if self.current_accel != ACCEL.NEUTRAL and acceleration == ACCEL.NEUTRAL:
            if self.current_accel == ACCEL.UP:
                data = b'R_UP'
            elif self.current_accel == ACCEL.DOWN:
                data = b'R_DOWN'



        if self.current_accel == ACCEL.NEUTRAL and acceleration != ACCEL.NEUTRAL:
            if acceleration == ACCEL.UP:
                data = b'P_UP'
            elif acceleration == ACCEL.DOWN:
                data = b'P_DOWN'

        if len(data) > 0:
            self.send_data(data)

        self.current_accel = acceleration



    def callback_yaw(self,*values):
        steering = STEER.NEUTRAL

        angle = values[0]

        if angle < - STEER_ANGLE_THRES:
            steering = STEER.RIGHT
        elif angle > STEER_ANGLE_THRES:
            steering = STEER.LEFT

        self.process_steering(steering)
    
    
    def callback_roll(self,*values):
        angle = values[0]

        acceleration = ACCEL.NEUTRAL

        if angle < ACCEL_ANGLE_OFFSET - ACCEL_ANGLE_THRES:
            acceleration = ACCEL.DOWN
        elif angle > ACCEL_ANGLE_OFFSET + ACCEL_ANGLE_THRES:
            acceleration = ACCEL.UP

        self.process_acceleration(acceleration)
    
    
    def callback_pitch(*values):
        return
   
   
   
    def callback_double_tap(self, *args):
        print(f"Touch callback called with args: {args}")
        current_time = time.time()
        
        if args and args[0] > 0:  # If touch count is greater than 0
            if (current_time - self.last_tap_time) < DOUBLE_TAP_THRESHOLD:
                self.tap_count += 1
                if self.tap_count == 2:
                    print("Double tap detected! Sending FIRE command.")
                    self.send_data(b'FIRE')
                    self.tap_count = 0
            else:
                self.tap_count = 1
            
            self.last_tap_time = current_time
        else:
            # Reset tap count if touch ended
            self.tap_count = 0
  
    def callback_yaw_shaker(self, *values):

        print("Received yaw values: {}".format(values))
        data = b''

        SHAKE_THRESHOLD = 5.0  # You may need to adjust this value based on your sensor's output


        current_yaw = values[0]
        yaw_difference = abs(current_yaw - self.previous_yaw)

        if yaw_difference > SHAKE_THRESHOLD:
            data = b'RESCUE'
            self.send_data(data)
            print("Shake detected!")

        self.previous_yaw = current_yaw
        
        
    def control_loop(self):
        """Infinite loop running at a target frequency to manage pressed and released commands."""
        target_frequency = 60  # Loop frequency in Hz (60Hz or adjust to 120Hz if needed)
        dt = 1.0 / target_frequency  # Time per loop iteration
        total_cycle_time = dt  # Total time for one cycle (pressed + released)

        while self.loop_running:
            # Update steering control
            self.update_control('steering', self.steering_value, total_cycle_time)
            # Update acceleration control
            self.update_control('accel', self.accel_value, total_cycle_time)
            time.sleep(dt)

    def update_control(self, control_type, current_value, total_cycle_time):
        """Update control states and send commands based on continuous input values."""
        # Determine the state variables based on control type
        if control_type == 'steering':
            direction = self.steering_direction
            state_attr = 'steering_state'
            timer_attr = 'steering_timer'
        elif control_type == 'accel':
            direction = self.accel_direction
            state_attr = 'accel_state'
            timer_attr = 'accel_timer'
        else:
            return

        # Initialize state and timer attributes if they don't exist
        if not hasattr(self, state_attr):
            setattr(self, state_attr, 'released')
        if not hasattr(self, timer_attr):
            setattr(self, timer_attr, 0.0)

        state = getattr(self, state_attr)
        timer = getattr(self, timer_attr)

        # Calculate t1 and t2 based on current_value
        t1 = current_value * total_cycle_time
        t2 = (1 - current_value) * total_cycle_time

        timer -= total_cycle_time  # Decrement timer

        if current_value == 0.0 or direction == STEER.NEUTRAL or direction == ACCEL.NEUTRAL:
            # Ensure the control is released
            if state == 'pressed':
                self.release_command(control_type, direction)
                state = 'released'
                timer = 0.0
        else:
            if timer <= 0:
                if state == 'pressed':
                    self.release_command(control_type, direction)
                    state = 'released'
                    timer = t2
                else:
                    self.press_command(control_type, direction)
                    state = 'pressed'
                    timer = t1

        # Update state and timer attributes
        setattr(self, state_attr, state)
        setattr(self, timer_attr, timer)

    def press_command(self, control_type, direction):
        """Send the 'pressed' command for the given control and direction."""
        if control_type == 'steering':
            if direction == STEER.LEFT:
                self.send_data(b'P_LEFT')
            elif direction == STEER.RIGHT:
                self.send_data(b'P_RIGHT')
        elif control_type == 'accel':
            if direction == ACCEL.UP:
                self.send_data(b'P_UP')
            elif direction == ACCEL.DOWN:
                self.send_data(b'P_DOWN')

    def release_command(self, control_type, direction):
        """Send the 'released' command for the given control and direction."""
        if control_type == 'steering':
            if direction == STEER.LEFT:
                self.send_data(b'R_LEFT')
            elif direction == STEER.RIGHT:
                self.send_data(b'R_RIGHT')
            # Reset steering direction if released
            self.steering_direction = STEER.NEUTRAL
        elif control_type == 'accel':
            if direction == ACCEL.UP:
                self.send_data(b'R_UP')
            elif direction == ACCEL.DOWN:
                self.send_data(b'R_DOWN')
            # Reset acceleration direction if released
            self.accel_direction = ACCEL.NEUTRAL



    # Callback methods for handling pad inputs
    def callback_x(self, *values):
        """Handle pad x-axis input for steering."""
        x = values[0]
        self.steering_value = min(abs(x), 1.0)  # Ensure value is between 0 and 1

        # Determine steering direction
        if x < -STEER_THRES:
            self.steering_direction = STEER.LEFT
        elif x > STEER_THRES:
            self.steering_direction = STEER.RIGHT
        else:
            self.steering_direction = STEER.NEUTRAL
            self.steering_value = 0.0  # No steering

    def callback_y(self, *values):
        """Handle pad y-axis input for acceleration."""
        y = values[0]
        self.accel_value = min(abs(y), 1.0)  # Ensure value is between 0 and 1

        # Determine acceleration direction
        if y < -ACCEL_THRES:
            self.accel_direction = ACCEL.DOWN  # Brake
        elif y > ACCEL_THRES:
            self.accel_direction = ACCEL.UP  # Accelerate
        else:
            self.accel_direction = ACCEL.NEUTRAL
            self.accel_value = 0.0  # No acceleration

    def callback_touchUP(self, *values):
        """Handle touch release event to reset controls."""
        # Reset steering and acceleration when touch is released
        self.steering_direction = STEER.NEUTRAL
        self.steering_value = 0.0
        self.accel_direction = ACCEL.NEUTRAL
        self.accel_value = 0.0


    def stop(self):
        """Stop the control loop and close the socket."""
        self.loop_running = False
        self.control_thread.join()
        self.client_socket.close()
        
        
        