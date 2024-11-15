import socket

import cv2

camera_id = 0
delay = 1
window_name = 'Turbo QR Detector'

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
address = ('localhost', 6006)

is_nitroing = False
frame_since_nitro = 0
max_frame_without_turbo = 20

qcd = cv2.QRCodeDetector()
cap = cv2.VideoCapture(camera_id)

while True:
    ret, frame = cap.read()

    view_nitro = False

    if ret:
        ret_qr, decoded_info, points, _ = qcd.detectAndDecodeMulti(frame)
        if ret_qr:
            for s, p in zip(decoded_info, points):
                if s:
                    if s == "NITRO":
                        view_nitro = True
                    color = (0, 255, 0)
                else:
                    color = (0, 0, 255)
                frame = cv2.polylines(frame, [p.astype(int)], True, color, 8)
        cv2.imshow(window_name, frame)

    # Handle the process of the Nitro Activation
    # If the QR Code was seen this frame
    if view_nitro:
        # Reset the nitro counter
        frame_since_nitro = 0

        # If the nitro is not already activated we send the command to the server
        if not is_nitroing:
            data = b'P_NITRO'
            client_socket.sendto(data, address)

    # If the QR wasn't seen this frame, we increase the nitro counter
    else:
        frame_since_nitro += 1
    # If the nitro counter is above the limit and the nitro is activated, we send the command to the server to stop the nitro
    if frame_since_nitro >= max_frame_without_turbo:
        if is_nitroing:
            data = b'R_NITRO'
            client_socket.sendto(data, address)
        is_nitroing = False


    if cv2.waitKey(delay) & 0xFF == ord('q'):
        break

cv2.destroyWindow(window_name)
