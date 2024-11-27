from oscpy.server import OSCThreadServer
import socket
import threading
from steering_acceleration import STEER, ACCEL
import time
import math


last_tap_time = 0
DOUBLE_TAP_THRESHOLD = 0.5  # Time in seconds between taps to consider it a double tap

#pad
STEER_THRES = 0.4
ACCEL_THRES = 0.4

#rotations
STEER_ANGLE_THRES = 20

ACCEL_ANGLE_THRES = 15
ACCEL_ANGLE_OFFSET = -50

class OSCServer:

    def __init__(self,is_collab):

        self.osc = OSCThreadServer(default_handler=self.dump)
        self.sock = self.osc.listen(address='127.0.0.1', port=8000, default=True)#c'est le server where the phone need to send its information on
        self.server_address = ('localhost', 6006)#STK_input_server
        self.variable_initialization()
        self.is_collab = is_collab

        if(self.is_collab):
          self.bind_callbacks_collab()
        else:    
          self.bind_callbacks_perf()


    def bind_callbacks_collab(self):
        self.osc.bind(b'/multisense/orientation/pitch', self.callback_pitch_right_left)
        self.osc.bind(b'/multisense/orientation/roll', self.callback_roll_acc)
        

      

    def bind_callbacks_perf(self):
        self.osc.bind(b'/multisense/orientation/yaw', self.callback_yaw_right_left)
        self.osc.bind(b'/multisense/pad/x', self.callback_x_lookBack_fire)
        self.osc.bind(b'/multisense/orientation/yaw', self.callback_yaw_shaker_rescue)


    def dump(self, address, *values):
        """Default handler for unbound OSC messages."""
        print(u'{}: {}'.format(
            address.decode('utf8'),
            ', '.join(
                '{}'.format(
                    v.decode('utf8') if isinstance(v, bytes) else v
                )
                for v in values if values
            )
        ))



    def stop(self):
        self.osc.stop()
        """Stop the control loop and close the socket."""
        self.loop_running = False
        self.control_thread.join()
        self.client_socket.close()



    def variable_initialization(self):
        self.current_steering = STEER.NEUTRAL
        self.current_accel = ACCEL.NEUTRAL
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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
            self.client_socket.sendto(data, self.server_address)

        

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



#coolab:

    def callback_pitch_right_left(self,*values):
        steering = STEER.NEUTRAL

        angle = values[0]

        if angle < - STEER_ANGLE_THRES:
            steering = STEER.RIGHT
        elif angle > STEER_ANGLE_THRES:
            steering = STEER.LEFT

        self.process_steering(steering)

    def callback_roll_acc(self,*values):
        angle = values[0]

        acceleration = ACCEL.NEUTRAL
        if angle < ACCEL_ANGLE_OFFSET - ACCEL_ANGLE_THRES:
            acceleration = ACCEL.NEUTRAL
        elif angle > ACCEL_ANGLE_OFFSET + ACCEL_ANGLE_THRES:
            acceleration = ACCEL.UP

        self.process_acceleration(acceleration)
    
#perfo:

    def callback_yaw_right_left(self,*values):
        steering = STEER.NEUTRAL

        angle = values[0]

        if angle < - STEER_ANGLE_THRES:
            steering = STEER.RIGHT
        elif angle > STEER_ANGLE_THRES:
            steering = STEER.LEFT

        self.process_steering(steering)

    def callback_x_lookBack_fire(self, *values):
        """Handle pad x-axis input for steering."""
        x = values[0]

        # Determine steering direction
        if x < -STEER_THRES:
            data = b'P_LOOKBACK'
        elif x > STEER_THRES:
            data = b'FIRE'
      
    def callback_yaw_shaker_rescue(self, *values):

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



