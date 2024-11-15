from oscpy.server import OSCThreadServer
from controller import Controller

class OSCServer:
    def __init__(self, controller, host='127.0.0.1', port=8000):
        self.osc = OSCThreadServer(default_handler=self.dump)
        self.sock = self.osc.listen(address=host, port=port, default=True)
        self.controller = controller

    def bind_callbacks(self):

        # # This section is for controlling the game with the pad
        self.osc.bind(b'/multisense/pad/x', self.controller.callback_x)
        self.osc.bind(b'/multisense/pad/y', self.controller.callback_y)
        self.osc.bind(b'/multisense/pad/touchUP', self.controller.callback_touchUP)


        # # This section is for controlling the game with orientation and firing with double tap
        # self.osc.bind(b'/multisense/orientation/yaw', self.controller.callback_yaw)
        # self.osc.bind(b'/multisense/orientation/roll', self.controller.callback_roll)
        # self.osc.bind(b'/multisense/orientation/pitch', self.controller.callback_pitch)

        ##For Shaker mvt
        # self.osc.bind(b'/multisense/orientation/yaw', self.controller.callback_yaw_shaker)

        ##For Continues mvt
        # self.osc.bind(b'/multisense/pad/x', self.controller.callback_x_continuous)
        # self.osc.bind(b'/multisense/pad/y', self.controller.callback_y_continuous)
        # self.osc.bind(b'/multisense/pad/touchUP', self.controller.callback_touchUP_continuous)

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
