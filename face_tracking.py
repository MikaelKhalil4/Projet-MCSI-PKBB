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
    def __init__(self):
        self.fl = 590
        self.screen_heigth = 21.6
        self.REAL_IPD = 6.3
        self.user_ipd = self.REAL_IPD

        if len(sys.argv) >= 2:
            self.user_ipd = float(sys.argv[1])

        print(f"Tracking initialized with an interpupillary distance of {self.user_ipd} cm")

        self.address = "127.0.0.1"
        self.port = 6006

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a UDP socket
        print("OSC connection established to " + self.address + " on port " + str(self.port) + "!")

        self.cap = cv2.VideoCapture(0)
        self.first_time = time.time() * 1000.0

        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # Width of the video frame
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # Height of the video frame
        print(f"Video size: {self.frame_width} x {self.frame_height}")
        self.res = TrackingResults()  # Create an instance of TrackingResults
        # Create a face detector instance with the live stream mode:
        base_options = python.BaseOptions(model_asset_path="blaze_face_short_range.tflite")
        options = vision.FaceDetectorOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.LIVE_STREAM,
            result_callback=self.res.get_result,  # Set the callback function to handle detection results
        )
        self.detector = vision.FaceDetector.create_from_options(options)  # Create the face detector
        self.MARGIN = 10  # pixels
        self.ROW_SIZE = 10  # pixels
        self.FONT_SIZE = 1
        self.FONT_THICKNESS = 2
        self.TEXT_COLOR = (255, 0, 0)  # red

    def compute3DPos(self, ibe_x, ibe_y, ipd_pixels):
        # compute the distance between the head and the camera
        z = (self.user_ipd * self.fl) / ipd_pixels  # Distance from the camera

        # compute the x and y coordinate in a Yup reference frame
        x = (ibe_x - self.frame_width / 2) * z / self.fl  # X coordinate in cm
        y = (ibe_y - self.frame_height / 2) * z / self.fl  # Y coordinate in cm

        return (x, y, z)

    def send_udp_command(self, command):
        # Send a command via UDP
        print(f"Sending command: {command}")
        self.sock.sendto(command.encode(), (self.address, self.port))

    def visualize(self, image, detection_result) -> np.ndarray:
        """Draws bounding boxes and keypoints on the input image and return it.
        Args:
          image: The input RGB image.
          detection_result: The list of all "Detection" entities to be visualize.
        Returns:
          Image with bounding boxes.
        """
        annotated_image = image.copy()
        height, width, _ = image.shape

        if detection_result is None or not detection_result.detections:
            # No detections to visualize; return the original image
            return annotated_image

        for detection in detection_result.detections:
            # Draw bounding_box
            bbox = detection.bounding_box
            start_point = bbox.origin_x, bbox.origin_y
            end_point = bbox.origin_x + bbox.width, bbox.origin_y + bbox.height
            cv2.rectangle(annotated_image, start_point, end_point, self.TEXT_COLOR, 3)

            # Draw keypoints
            for keypoint in detection.keypoints:
                keypoint_px = _normalized_to_pixel_coordinates(
                    keypoint.x, keypoint.y, width, height
                )
                if keypoint_px is not None:
                    color, thickness, radius = (0, 255, 0), 2, 2
                    cv2.circle(annotated_image, keypoint_px, radius, color, thickness)

            # Draw only the keypoints corresponding to the eyes
            right_eye = detection.keypoints[0]
            left_eye = detection.keypoints[1]
            right_eye_px = _normalized_to_pixel_coordinates(
                right_eye.x, right_eye.y, width, height
            )
            left_eye_px = _normalized_to_pixel_coordinates(
                left_eye.x, left_eye.y, width, height
            )

            # Draw the eyes with a specific color (green)
            eye_color = (0, 255, 0)  # Green color for eyes
            thickness = 2
            radius = 2
            if right_eye_px and left_eye_px:
                cv2.circle(annotated_image, right_eye_px, radius, eye_color, thickness)
                cv2.circle(annotated_image, left_eye_px, radius, eye_color, thickness)

                # Draw the center of the eyes with a different color
                center_eye_px = (
                    int((right_eye_px[0] + left_eye_px[0]) / 2),
                    int((right_eye_px[1] + left_eye_px[1]) / 2),
                )
                center_color = (255, 0, 0)  # Blue color for center
                cv2.circle(annotated_image, center_eye_px, radius, center_color, thickness)

            # Draw label and score
            category = detection.categories[0]
            category_name = category.category_name
            category_name = "" if category_name is None else category_name
            probability = round(category.score, 2)
            result_text = category_name + " (" + str(probability) + ")"
            text_location = (
                self.MARGIN + bbox.origin_x,
                self.MARGIN + self.ROW_SIZE + bbox.origin_y,
            )
            cv2.putText(
                annotated_image,
                result_text,
                text_location,
                cv2.FONT_HERSHEY_PLAIN,
                self.FONT_SIZE,
                self.TEXT_COLOR,
                self.FONT_THICKNESS,
            )

        return annotated_image

    def runtracking(self):
        print("\nTracking started !!!")
        print("Hit ESC key to quit...")
        # Variables to track the previous head state
        previous_left = False
        previous_right = False
        previous_accelerate = False
        previous_brake = False
        # infinite loop for processing the video stream
        while True:
            # add to delay to avoid that the loop run too fast
            time.sleep(0.05)

            # read one frame from a camera and get the frame timestamp
            ret, img_bgr = self.cap.read()
            frame_timestamp_ms = int(time.time() * 1000 - self.first_time)

            #! we added on purpose this flip, to remove the mirror effect
            img_bgr = cv2.flip(img_bgr, 1)
            # Convert the opencv image to RGB
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

            # Convert the frame received from OpenCV to a MediaPipe’s Image object.
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

            # Send live image data to perform face detection.
            # The results are accessible via the `result_callback` provided in
            # the `FaceDetectorOptions` object.
            # The face detector must be created with the live stream mode.
            self.detector.detect_async(
                mp_image, int(time.time() * 1000)
            )  # Perform asynchronous face detection

            if self.res.tracking_results and self.res.tracking_results.detections:
                # If a face is detected
                # Get the biggest face
                biggest_face = max(
                    self.res.tracking_results.detections,
                    key=lambda d: d.bounding_box.width * d.bounding_box.height,
                )
                # Get the position of the two eyes in pixels
                right_eye = biggest_face.keypoints[0]  # Get right eye keypoint
                left_eye = biggest_face.keypoints[1]  # Get left eye keypoint
                # If we have a position for the two eyes
                # compute the position between the two eyes (in pixels)
                right_eye_px = _normalized_to_pixel_coordinates(
                    right_eye.x, right_eye.y, self.frame_width, self.frame_height
                )
                left_eye_px = _normalized_to_pixel_coordinates(
                    left_eye.x, left_eye.y, self.frame_width, self.frame_height
                )
                # compute the interpupillary distance (in pixels)
                if right_eye_px and left_eye_px:
                    ipd_pixels = math.hypot(
                        right_eye_px[0] - left_eye_px[0], right_eye_px[1] - left_eye_px[1]
                    )
                    # Compute the 3D position of the user's head
                    ibe_x = (right_eye_px[0] + left_eye_px[0]) / 2
                    ibe_y = (right_eye_px[1] + left_eye_px[1]) / 2
                    pos_x, pos_y, pos_z = self.compute3DPos(ibe_x, ibe_y, ipd_pixels)
                    print(f"3D position: {pos_x:.2f} - {pos_y:.2f} - {pos_z:.2f}")

                    # Head movements mapped to game controls
                    if pos_x > 2:  # Turn right
                        if not previous_right:
                            self.send_udp_command("P_RIGHT")  # Press right
                            previous_right = True
                        if previous_left:  # Release left if previously pressed
                            self.send_udp_command("R_LEFT")
                            previous_left = False
                    elif pos_x < -2:  # Turn left
                        if not previous_left:
                            self.send_udp_command("P_LEFT")  # Press left
                            previous_left = True
                        if previous_right:  # Release right if previously pressed
                            self.send_udp_command("R_RIGHT")
                            previous_right = False
                    else:  # Head is centered, release both left and right
                        if previous_left:
                            self.send_udp_command("R_LEFT")
                            previous_left = False
                        if previous_right:
                            self.send_udp_command("R_RIGHT")
                            previous_right = False

                    if pos_z < 30:  # Accelerate (close to the camera)
                        if not previous_accelerate:
                            self.send_udp_command("P_ACCELERATE")
                            previous_accelerate = True
                    elif pos_z > 40:  # Brake (far from the camera)
                        if not previous_brake:
                            self.send_udp_command("P_BRAKE")
                            previous_brake = True
                        if previous_accelerate:  # Release accelerate
                            self.send_udp_command("R_ACCELERATE")
                            previous_accelerate = False
                    else:  # Neither brake nor accelerate
                        if previous_brake:
                            self.send_udp_command("R_BRAKE")
                            previous_brake = False
                        if previous_accelerate:
                            self.send_udp_command("R_ACCELERATE")
                            previous_accelerate = False
                else:
                    print("Invalid interpupillary distance.")
            else:
                print("No face detected.")

            # Display the image with or without annotations
            annotated_image = mp_image.numpy_view()
            annotated_image = self.visualize(annotated_image, self.res.tracking_results)
            bgr_annotated_image = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
            cv2.imshow('img', bgr_annotated_image)

            # Wait for Esc key to stop
            k = cv2.waitKey(30) & 0xFF
            if k == 27:
                break

        # release the video stream from the camera
        self.cap.release()
        # close the associated window
        cv2.destroyAllWindows()


def _normalized_to_pixel_coordinates(
    normalized_x: float, normalized_y: float, image_width: int, image_height: int
) -> Union[None, Tuple[int, int]]:
    """Converts normalized value pair to pixel coordinates."""
    if not (0 <= normalized_x <= 1 and 0 <= normalized_y <= 1):
        return None

    x_px = min(math.floor(normalized_x * image_width), image_width - 1)
    y_px = min(math.floor(normalized_y * image_height), image_height - 1)
    return x_px, y_px


# Create a new class for retrieving and storing the tracking results
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




