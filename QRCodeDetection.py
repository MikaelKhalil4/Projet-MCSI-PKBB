import socket
import threading
import cv2

camera_id = 0
delay = 1
window_name = 'Turbo QR Detector'

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
address = ('localhost', 6006)

qcd = cv2.QRCodeDetector()
cap = cv2.VideoCapture(camera_id)

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

is_nitroing = False
frame_since_nitro = 0
max_frame_without_turbo = 20

is_skidding = False
frame_since_skidding = 0
max_frame_without_skidding = 20

is_lookbacking = False
frame_since_lookback = 0
max_frame_without_lookback = 20


has_fired = False
has_rescued = False

def Recognize_QR_Code(frame):
    global is_lookbacking, is_skidding, is_nitroing, frame_since_lookback, frame_since_skidding, frame_since_nitro, has_fired, has_rescued

    view_nitro = False
    view_skidding = False
    view_lookback = False


    ret_qr, decoded_info, points, _ = qcd.detectAndDecodeMulti(frame)

    if ret_qr:
        for s, p in zip(decoded_info, points):
            if s:
                if s == "NITRO":
                    view_nitro = True
                    frame_since_nitro = 0
                elif s == "SKIDDING":
                    view_skidding = True
                    frame_since_skidding = 0
                elif s == "LOOKBACK":
                    view_lookback = True
                    frame_since_lookback = 0
                elif s == "FIRE":
                    if not has_fired:
                        SendInstantCommande("P_FIRE")
                        has_fired = True
                elif s == "RESCUE":
                    if not has_rescued:
                        SendInstantCommande("P_RESCUE")
                        has_rescued = True
                else:
                    print("Unknown QR Code : " + s)
                color = (0, 255, 0)
            else:
                color = (0, 0, 255)
            frame = cv2.polylines(frame, [p.astype(int)], True, color, 8)

    # Handle the commands
    HandleNitro(view_nitro)
    HandleSkidding(view_skidding)
    HandleLookback(view_lookback)

def HandleNitro(view_nitro):
    global is_nitroing, frame_since_nitro, max_frame_without_turbo
    # If the QR Code was seen this frame
    if view_nitro:
        # Reset the nitro counter
        frame_since_nitro = 0

        # If the nitro is not already activated we send the command to the server
        if not is_nitroing:
            data = b'P_NITRO'
            client_socket.sendto(data, address)
            is_nitroing = True

    # If the QR wasn't seen this frame, we increase the nitro counter
    else:
        frame_since_nitro += 1
    # If the nitro counter is above the limit and the nitro is activated, we send the command to the server to stop the nitro
    if frame_since_nitro >= max_frame_without_turbo:
        if is_nitroing:
            data = b'R_NITRO'
            client_socket.sendto(data, address)
        is_nitroing = False

def HandleSkidding(view_skidding):
    global is_skidding, frame_since_skidding, max_frame_without_skidding
    # If the QR Code was seen this frame
    if view_skidding:
        # Reset the skidding counter
        frame_since_skidding = 0

        # If the skidding is not already activated we send the command to the server
        if not is_skidding:
            data = b'P_SKIDDING'
            client_socket.sendto(data, address)
            is_skidding = True

    # If the QR wasn't seen this frame, we increase the skidding counter
    else:
        frame_since_skidding += 1
    # If the skidding counter is above the limit and the skidding is activated, we send the command to the server to stop the skidding
    if frame_since_skidding >= max_frame_without_skidding:
        if is_skidding:
            data = b'R_SKIDDING'
            client_socket.sendto(data, address)
        is_skidding = False

def HandleLookback(view_lookback):
    global is_lookbacking, frame_since_lookback, max_frame_without_lookback
    # If the QR Code was seen this frame
    if view_lookback:
        # Reset the lookback counter
        frame_since_lookback = 0

        # If the lookback is not already activated we send the command to the server
        if not is_lookbacking:
            data = b'P_LOOKBACK'
            client_socket.sendto(data, address)
            is_lookbacking = True

    # If the QR wasn't seen this frame, we increase the lookback counter
    else:
        frame_since_lookback += 1
    # If the lookback counter is above the limit and the lookback is activated, we send the command to the server to stop the lookback
    if frame_since_lookback >= max_frame_without_lookback:
        if is_lookbacking:
            data = b'R_LOOKBACK'
            client_socket.sendto(data, address)
        is_lookbacking = False

def SendInstantCommande(commande):
    global has_fired, has_rescued
    if commande == "P_RESCUE":
        data = b'P_RESCUE'
        client_socket.sendto(data, address)
        # Programme un envoie de la commande R_RESCUE dans 2 secondes
        delay = 2
        timer = threading.Timer(delay, SendInstantCommande, ["R_RESCUE"])
        timer.start()

    elif commande == "P_FIRE":
        data = b'P_FIRE'
        client_socket.sendto(data, address)
        # Programme un envoie de la commande R_FIRE dans 2 secondes
        delay = 2
        timer = threading.Timer(delay, SendInstantCommande, ["R_FIRE"])
        timer.start()

    elif commande == "R_RESCUE":
        data = b'R_RESCUE'
        client_socket.sendto(data, address)
        has_rescued = False

    elif commande == "R_FIRE":
        data = b'R_FIRE'
        client_socket.sendto(data, address)
        has_fired = False


while True:
    ret, frame = cap.read()


    if ret:
        Recognize_QR_Code(frame)
        cv2.imshow(window_name, frame)


    if cv2.waitKey(delay) & 0xFF == ord('q'):
        break

cv2.destroyWindow(window_name)
