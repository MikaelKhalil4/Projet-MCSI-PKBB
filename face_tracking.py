######################################################################################
# This python script implements a 3D face tracking which uses a webcam               #
# to achieve face detection. This face detection is done with MediaPipe:             #
#                                                                                    #
# The script then streams the 3D position through OSC                                #
#                                                                                    #
# date: December 2019                                                                #
# authors: Cedric Fleury                                                             #
# affiliation: IMT Atlantique, Lab-STICC (Brest)                                     #
#                                                                                    #
# usage: python tracking.py x                                                        #
# where x is an optional value to tune the interpupillary distance of the            #
# tracked subject (by default, the interpupillary distance is set at 6cm).           #
######################################################################################

# import necessary modules
import socket
import sys
import time
import math
import threading
import numpy as np
from typing import Tuple, Union

# import oscpy for OSC streaming (https://pypi.org/project/ocspy/)
from oscpy.client import OSCClient

# import opencv for image processing
import cv2

# import mediapipe for face detection
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


class FaceTracking:
    def __init__(self, user_ipd=6.3, address="127.0.0.1", port=6006, model_path="blaze_face_short_range.tflite"):
        # Constants
        self.REAL_IPD = 6.3  # Interpupillary distance in cm
        self.screen_height = 21.6  # Screen height in cm
        self.fl = 590  # Camera focal length in pixels
        
        # User-configured parameters
        self.user_ipd = user_ipd
        self.address = address
        self.port = port
        
        # OSC connection
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"OSC connection established to {self.address} on port {self.port}!")
        
        # Video capture
        self.cap = cv2.VideoCapture(0)
        self.first_time = time.time() * 1000.0
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Video size: {self.frame_width} x {self.frame_height}")
        
        # MediaPipe configuration
        self.results = TrackingResults()
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceDetectorOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.LIVE_STREAM,
            result_callback=self.results.get_result,
        )
        self.detector = vision.FaceDetector.create_from_options(options)
    
    def send_udp_command(self, command):
        print(f"Sending command: {command}")
        self.sock.sendto(command.encode(), (self.address, self.port))
    
    def compute3DPos(self, ibe_x, ibe_y, ipd_pixels):
        z = (self.user_ipd * self.fl) / ipd_pixels
        x = (ibe_x - self.frame_width / 2) * z / self.fl
        y = (ibe_y - self.frame_height / 2) * z / self.fl
        return x, y, z
    
    def runtracking(self):
        print("\nTracking started!")
        print("Hit ESC key to quit...")

        previous_left = previous_right = previous_accelerate = previous_brake = False

        while True:
            time.sleep(0.05)
            ret, img_bgr = self.cap.read()
            frame_timestamp_ms = int(time.time() * 1000 - self.first_time)

            img_bgr = cv2.flip(img_bgr, 1)
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

            self.detector.detect_async(mp_image, frame_timestamp_ms)

            if self.results.tracking_results and self.results.tracking_results.detections:
                biggest_face = max(
                    self.results.tracking_results.detections,
                    key=lambda d: d.bounding_box.width * d.bounding_box.height,
                )
                right_eye = biggest_face.keypoints[0]
                left_eye = biggest_face.keypoints[1]
                right_eye_px = _normalized_to_pixel_coordinates(
                    right_eye.x, right_eye.y, self.frame_width, self.frame_height
                )
                left_eye_px = _normalized_to_pixel_coordinates(
                    left_eye.x, left_eye.y, self.frame_width, self.frame_height
                )

                if right_eye_px and left_eye_px:
                    ipd_pixels = math.hypot(
                        right_eye_px[0] - left_eye_px[0], right_eye_px[1] - left_eye_px[1]
                    )
                    ibe_x = (right_eye_px[0] + left_eye_px[0]) / 2
                    ibe_y = (right_eye_px[1] + left_eye_px[1]) / 2

                    if ipd_pixels != 0:
                        pos_x, pos_y, pos_z = self.compute3DPos(ibe_x, ibe_y, ipd_pixels)
                        print(f"3D position: {pos_x:.2f} - {pos_y:.2f} - {pos_z:.2f}")

                        # Example control logic
                        if pos_x > 10:  # Turn right
                            if not previous_right:
                                self.send_udp_command("P_LOOKBACK")
                                previous_right = True
                            if previous_left:
                                self.send_udp_command("R_LOOKBACK")
                                previous_left = False
                        elif pos_x < -10:  # Turn left
                            if not previous_left:
                                self.send_udp_command("P_LOOKBACK")
                                previous_left = True
                            if previous_right:
                                self.send_udp_command("R_LOOKBACK")
                                previous_right = False
                        else:
                            if previous_left:
                                self.send_udp_command("R_LOOKBACK")
                                previous_left = False
                            if previous_right:
                                self.send_udp_command("R_LOOKBACK")
                                previous_right = False

                        if pos_z < 30:  # Accelerate
                            if not previous_accelerate:
                                self.send_udp_command("P_ACCELERATE")
                                previous_accelerate = True
                        else:
                            if previous_accelerate:
                                self.send_udp_command("R_ACCELERATE")
                                previous_accelerate = False
                    else:
                        print("Invalid interpupillary distance.")
            else:
                print("No face detected.")

            annotated_image = mp_image.numpy_view()
            annotated_image = visualize(annotated_image, self.results.tracking_results)
            bgr_annotated_image = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
            cv2.imshow('img', bgr_annotated_image)

            if cv2.waitKey(30) & 0xFF == 27:  # ESC key
                break

        self.cap.release()
        cv2.destroyAllWindows()


class TrackingResults:
    tracking_results = None

    def get_result(
        self,
        result: vision.FaceDetectorResult,
        output_image: mp.Image,
        timestamp_ms: int,
    ):
        # Callback function to store the face detection results
        self.tracking_results = result

