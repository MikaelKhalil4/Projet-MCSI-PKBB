import socket
import threading
import cv2


class QRDetector:
    """

    Ce code permet d'ouvrir un flux webcam et de détecter des QR Codes sur l'image. Il envoie alors une commande
    au STK_input_server suivant le message dans le QR Code detecté.
    QR Code implémentés :
    - Usage instantané :
        - "FIRE" : Active le tir
        - "RESCUE" : Active le mode rescue
    - Usage en continu :
        - "NITRO" : Active le turbo
        - "SKIDDING" : Active le drift
        - "LOOKBACK" : Active le regard en arrière
    """

    def __init__(self, _server_address='localhost', _server_port=6007):

        self.camera_id = 0
        self.delay = 1
        self.window_name = 'QR Code Detector'

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_address = (_server_address, _server_port)

        self.qcd = cv2.QRCodeDetector()
        self.cap = cv2.VideoCapture(self.camera_id)

        self.release_delay = 0.1

        self.is_nitroing = False
        self.frame_since_nitro = 0
        self.max_frame_without_turbo = 20

        self.is_skidding = False
        self.frame_since_skidding = 0
        self.max_frame_without_skidding = 20

        self.is_lookbacking = False
        self.frame_since_lookback = 0
        self.max_frame_without_lookback = 20

        self.has_fired = False
        self.has_rescued = False

    def recognize_qr_code(self, frame):

        view_nitro = False
        view_skidding = False
        view_lookback = False

        ret_qr, decoded_info, points, _ = self.qcd.detectAndDecodeMulti(frame)

        if ret_qr:
            for s, p in zip(decoded_info, points):
                if s:
                    if s == "NITRO":
                        view_nitro = True
                        self.frame_since_nitro = 0
                    elif s == "SKIDDING":
                        view_skidding = True
                        self.frame_since_skidding = 0
                    elif s == "LOOKBACK":
                        view_lookback = True
                        self.frame_since_lookback = 0
                    elif s == "FIRE":
                        if not self.has_fired:
                            self.send_instant_commande("P_FIRE")
                            self.has_fired = True
                    elif s == "RESCUE":
                        if not self.has_rescued:
                            self.send_instant_commande("P_RESCUE")
                            self.has_rescued = True
                    else:
                        print("Unknown QR Code : " + s)
                    color = (0, 255, 0)
                else:
                    color = (0, 0, 255)
                frame = cv2.polylines(frame, [p.astype(int)], True, color, 8)

        # Handle the commands
        self.handle_nitro(view_nitro)
        self.handle_skidding(view_skidding)
        self.handle_lookback(view_lookback)

    def handle_nitro(self, view_nitro):
        # If the QR Code was seen this frame
        if view_nitro:
            # Reset the nitro counter
            self.frame_since_nitro = 0

            # If the nitro is not already activated we send the command to the server
            if not self.is_nitroing:
                data = b'P_NITRO'
                self.client_socket.sendto(data, self.server_address)
                self.is_nitroing = True

        # If the QR wasn't seen this frame, we increase the nitro counter
        else:
            self.frame_since_nitro += 1
        # If the nitro counter is above the limit and the nitro is activated, we send the command to the server to
        # stop the nitro
        if self.frame_since_nitro >= self.max_frame_without_turbo:
            if self.is_nitroing:
                data = b'R_NITRO'
                self.client_socket.sendto(data, self.server_address)
            self.is_nitroing = False

    def handle_skidding(self, view_skidding):
        # If the QR Code was seen this frame
        if view_skidding:
            # Reset the skidding counter
            self.frame_since_skidding = 0

            # If the skidding is not already activated we send the command to the server
            if not self.is_skidding:
                data = b'P_SKIDDING'
                self.client_socket.sendto(data, self.server_address)
                self.is_skidding = True

        # If the QR wasn't seen this frame, we increase the skidding counter
        else:
            self.frame_since_skidding += 1
        # If the skidding counter is above the limit and the skidding is activated, we send the command to the server
        # to stop the skidding
        if self.frame_since_skidding >= self.max_frame_without_skidding:
            if self.is_skidding:
                data = b'R_SKIDDING'
                self.client_socket.sendto(data, self.server_address)
            self.is_skidding = False

    def handle_lookback(self, view_lookback):
        # If the QR Code was seen this frame
        if view_lookback:
            # Reset the lookback counter
            self.frame_since_lookback = 0

            # If the lookback is not already activated we send the command to the server
            if not self.is_lookbacking:
                data = b'P_LOOKBACK'
                self.client_socket.sendto(data, self.server_address)
                self.is_lookbacking = True

        # If the QR wasn't seen this frame, we increase the lookback counter
        else:
            self.frame_since_lookback += 1
        # If the lookback counter is above the limit and the lookback is activated, we send the command to the server
        # to stop the lookback
        if self.frame_since_lookback >= self.max_frame_without_lookback:
            if self.is_lookbacking:
                data = b'R_LOOKBACK'
                self.client_socket.sendto(data, self.server_address)
            self.is_lookbacking = False

    def send_instant_commande(self, command):
        if command == "P_RESCUE":
            data = b'P_RESCUE'
            self.client_socket.sendto(data, self.server_address)
            # Programme un envoie de la commande R_RESCUE dans 2 secondes
            timer = threading.Timer(self.release_delay, self.send_instant_commande, ["R_RESCUE"])
            timer.start()

        elif command == "P_FIRE":
            data = b'P_FIRE'
            self.client_socket.sendto(data, self.server_address)
            # Programme un envoie de la commande R_FIRE dans 2 secondes
            timer = threading.Timer(self.release_delay, self.send_instant_commande, ["R_FIRE"])
            timer.start()

        elif command == "R_RESCUE":
            data = b'R_RESCUE'
            self.client_socket.sendto(data, self.server_address)
            self.has_rescued = False

        elif command == "R_FIRE":
            data = b'R_FIRE'
            self.client_socket.sendto(data, self.server_address)
            self.has_fired = False

    def run(self):
        while True:
            ret, frame = self.cap.read()

            if ret:
                self.recognize_qr_code(frame)
                cv2.imshow(self.window_name, frame)

            if cv2.waitKey(self.delay) & 0xFF == ord('q'):
                break

        cv2.destroyWindow(self.window_name)
