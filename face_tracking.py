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


########## Part 3: compute the focal length of the webcam ###########

# define the camera focal length in pixels
# Use the calbirate.py script to determine it!
fl = 590


################## Part 4: compute the 3D position ##################

# define the height of your screen in cm
screen_heigth = 21.6

# define the default interpupillary distance
REAL_IPD = 6.3  # Interpupillary distance in cm (average human IPD)

# Set the default interpupillary distance from user input or default
user_ipd = REAL_IPD

if len(sys.argv) >= 2:
    user_ipd = float(sys.argv[1])

print(f"Tracking initialized with an interpupillary distance of {user_ipd} cm")


# define address and port for streaming
address = "127.0.0.1"
port = 6006

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a UDP socket
print("OSC connection established to " + address + " on port " + str(port) + "!")


# capture frames from a camera and the time
cap = cv2.VideoCapture(0)
first_time = time.time() * 1000.0

# Get image size
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # Width of the video frame
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # Height of the video frame
print(f"Video size: {frame_width} x {frame_height}")


################# Part 1: understand how the face dectector works #################


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


res = TrackingResults()  # Create an instance of TrackingResults

# Create a face detector instance with the live stream mode:
base_options = python.BaseOptions(model_asset_path="blaze_face_short_range.tflite")
options = vision.FaceDetectorOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.LIVE_STREAM,
    result_callback=res.get_result,  # Set the callback function to handle detection results
)
detector = vision.FaceDetector.create_from_options(options)  # Create the face detector


#### visualization fonctions ####

MARGIN = 10  # pixels
ROW_SIZE = 10  # pixels
FONT_SIZE = 1
FONT_THICKNESS = 2
TEXT_COLOR = (255, 0, 0)  # red



def _normalized_to_pixel_coordinates(
    normalized_x: float, normalized_y: float, image_width: int, image_height: int
) -> Union[None, Tuple[int, int]]:
    """Converts normalized value pair to pixel coordinates."""

    # Checks if the float value is between 0 and 1.
    def is_valid_normalized_value(value: float) -> bool:
        return (value > 0 or math.isclose(0, value)) and (
            value < 1 or math.isclose(1, value)
        )

    if not (
        is_valid_normalized_value(normalized_x)
        and is_valid_normalized_value(normalized_y)
    ):
        # TODO: Draw coordinates even if it's outside of the image bounds: DONE
        x_px = math.floor(normalized_x * image_width)
        y_px = math.floor(normalized_y * image_height)
        return x_px, y_px

    x_px = min(math.floor(normalized_x * image_width), image_width - 1)
    y_px = min(math.floor(normalized_y * image_height), image_height - 1)
    return x_px, y_px


def visualize(image, detection_result) -> np.ndarray:
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
        cv2.rectangle(annotated_image, start_point, end_point, TEXT_COLOR, 3)

        # Draw keypoints
        for keypoint in detection.keypoints:
            keypoint_px = _normalized_to_pixel_coordinates(
                keypoint.x, keypoint.y, width, height
            )
            color, thickness, radius = (0, 255, 0), 2, 2
            cv2.circle(annotated_image, keypoint_px, thickness, color, radius)
        # TODO: comment the previous section

        # The previous section draws all keypoints in green with a radius of 2 and thickness of 2.

        #### Part 2: get the position of the eyes and compute the center of the eyes ####
        # Draw only the keypoints corresponding to the eyes
        # TODO......
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
        # TODO......
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
        text_location = (MARGIN + bbox.origin_x, MARGIN + ROW_SIZE + bbox.origin_y)
        cv2.putText(
            annotated_image,
            result_text,
            text_location,
            cv2.FONT_HERSHEY_PLAIN,
            FONT_SIZE,
            TEXT_COLOR,
            FONT_THICKNESS,
        )

    return annotated_image


#####################################################################################

######################### Part 4: compute the 3D position ###########################


# convert the 2D position in pixels in the image to
# a 3D position in cm in the camera reference frame
def compute3DPos(ibe_x, ibe_y, ipd_pixels):

    # compute the distance between the head and the camera
    # TODO...
    z = (user_ipd * fl) / ipd_pixels  # Distance from the camera

    # compute the x and y coordinate in a Yup reference frame
    # TODO...
    x = (ibe_x - frame_width / 2) * z / fl  # X coordinate in cm
    y = (ibe_y - frame_height / 2) * z / fl  # Y coordinate in cm

    # center the reference frame on the center of the screen
    # (and not on the camera)
    # TODO...
    screen_center_offset_x = frame_width / 2
    screen_center_offset_y = frame_height / 2

    x_centered = x - screen_center_offset_x
    y_centered = y - screen_center_offset_y

    return (x, y, z)


################################ main fonction ##############################
# Helper function to send UDP commands
def send_udp_command(command):
    # Send a command via UDP
    print(f"Sending command: {command}")
    sock.sendto(command.encode(), (address, port))

def runtracking():

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
        ret, img_bgr = cap.read()
        frame_timestamp_ms = int(time.time() * 1000 - first_time)

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
        detector.detect_async(
            mp_image, int(time.time() * 1000)
        )  # Perform asynchronous face detection

        if res.tracking_results and res.tracking_results.detections:
            #### Part 2: get the position of the eyes and compute the center of the eyes ####

            # If a face is detected
            # Get the biggest face
            # TODO....
            biggest_face = max(
                res.tracking_results.detections,
                key=lambda d: d.bounding_box.width * d.bounding_box.height,
            )
            # Get the position of the two eyes in pixels
            # TODO....
            right_eye = biggest_face.keypoints[0]  # Get right eye keypoint
            left_eye = biggest_face.keypoints[1]  # Get left eye keypoint
            # If we have a position for the two eyes
            # compute the position between the two eyes (in pixels)
            # TODO....
            right_eye_px = _normalized_to_pixel_coordinates(
                right_eye.x, right_eye.y, frame_width, frame_height
            )
            left_eye_px = _normalized_to_pixel_coordinates(
                left_eye.x, left_eye.y, frame_width, frame_height
            )
            # compute the interpupillary distance (in pixels)
            # TODO....
            if right_eye_px and left_eye_px:
                ipd_pixels = math.hypot(
                    right_eye_px[0] - left_eye_px[0], right_eye_px[1] - left_eye_px[1]
                )
            ###################### Part 4: compute the 3D position ###########################
            # compute the 3D position in the reference frame of the screen center
            # pos_x, pos_y, pos_z =
            # TODO...
            if right_eye_px and left_eye_px:
                ibe_x = (right_eye_px[0] + left_eye_px[0]) / 2
                ibe_y = (right_eye_px[1] + left_eye_px[1]) / 2

            ################### Part 5: send the head position with OSC ######################
            # clientOSC.send_message(b'/tracker/head/pos_xyz', [pos_x, pos_y, pos_z])
            # TODO ...
            if ipd_pixels != 0:
                # Compute the 3D position of the user's head
                pos_x, pos_y, pos_z = compute3DPos(ibe_x, ibe_y, ipd_pixels)
                print(f"3D position: {pos_x:.2f} - {pos_y:.2f} - {pos_z:.2f}")

                # Head movements mapped to game controls
                if pos_x > 10:  # Turn right
                    if not previous_right:
                        send_udp_command("P_LOOKBACK")  # Press right
                        previous_right = True
                    if previous_left:  # Release left if previously pressed
                        send_udp_command("P_LOOKBACK")
                        previous_left = False
                elif pos_x < -10:  # Turn left
                    if not previous_left:
                        send_udp_command("P_LOOKBACK")  # Press left
                        previous_left = True
                    if previous_right:  # Release right if previously pressed
                        send_udp_command("P_LOOKBACK")
                        previous_right = False
                else:  # Head is centered, release both left and right
                    if previous_left:
                        send_udp_command("R_LOOKBACK")
                        previous_left = False
                    if previous_right:
                        send_udp_command("R_LOOKBACK")
                        previous_right = False

                if pos_z < 30:  # Accelerate (close to the camera)
                    if not previous_accelerate:
                        send_udp_command("P_BRAKE")
                        previous_brake = True
                else:  # Neither brake nor accelerate
                    if previous_brake:
                        send_udp_command("R_BRAKE")
                        previous_brake = False
            else:
                print("Invalid interpupillary distance.")                          
        else:
          print("No face detected.")
            
        # Display the image with or without annotations
        annotated_image = mp_image.numpy_view()
        annotated_image = visualize(annotated_image, res.tracking_results)
        bgr_annotated_image = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
        cv2.imshow('img', bgr_annotated_image)

        # Wait for Esc key to stop
        k = cv2.waitKey(30) & 0xff
        if k == 27:
            break

    # release the video stream from the camera


  cap.release()
  # close the associated window
  cv2.destroyAllWindows()


############################ program execution #############################

runtracking()
