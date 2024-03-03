import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os
import cv2
import pygame
import sys
from pygame.locals import QUIT
import time  # Import the time module

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
HandLandmarkerResult = mp.tasks.vision.HandLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode
Delegate = mp.tasks.BaseOptions.Delegate

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
HAND_LANDMARKER_PATH = os.path.join(PROJECT_ROOT, "models/hand_landmarker.task")

ready = True
def print_result(result: HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    global ready
    ready = True
    hand_count = len(result.handedness)
    if  hand_count == 0:
        print("No Hand")
    else:
        print(f"{hand_count} hands")

base_options = python.BaseOptions(model_asset_path=HAND_LANDMARKER_PATH, delegate=Delegate.CPU)
options = vision.HandLandmarkerOptions(base_options=base_options,
                                       num_hands=2,
                                       running_mode=VisionRunningMode.LIVE_STREAM,
                                       result_callback=print_result)
detector = vision.HandLandmarker.create_from_options(options)

pygame.init()

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise Exception("Could not open video device")

ret, frame = cap.read()
print(frame.shape)
height = frame.shape[0] // 2
width = frame.shape[1] // 2

window_size = (width, height)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption('Camera Feed')

start_time = time.time()  # Capture the start time

running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Calculate the current timestamp in milliseconds
    current_time = time.time()
    timestamp_ms = int((current_time - start_time) * 1000)  # Elapsed time in milliseconds

    if ready:
        ready = False
        detection_result = detector.detect_async(
            mp.Image(data=frame, image_format=mp.ImageFormat.SRGB),
            timestamp_ms)  # Pass the timestamp in milliseconds
    else:
        print("Frame skipped, not ready")

    frame = frame[::2, ::2]
    frame = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")
    screen.blit(frame, (0, 0))
    pygame.display.flip()

cap.release()
pygame.quit()
sys.exit()
