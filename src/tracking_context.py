from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerResult
from cv2 import VideoCapture
from os import path
from typing import Callable
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerResult, HandLandmarkerOptions, RunningMode
from pygame import time
import numpy as np
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2

class TrackingContext:
    camera: VideoCapture | None
    hand_landmarker: HandLandmarker
    hands: HandLandmarkerResult | None
    hands_last_seen_ms: int | None

    def __init__(self, root_dir: str, camera: VideoCapture | None = None):
        self.camera = camera
        self.hand_landmarker = TrackingContext.create_hand_detector(root_dir, self.hand_landmarker_callback)
        self.frame = None
        self.hands = None
        self.hands_last_seen_ms = None
    
    def hand_landmarker_callback(self, result: HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
        self.hands = result

        if len(result.handedness) > 0:
            self.hands_last_seen_ms = timestamp_ms
    
    def update(self, timestamp_ms: int):
        if self.camera is not None and self.camera.isOpened():
            got_frame, frame = self.camera.read()

            if got_frame:
                self.frame = frame
                self.hand_landmarker.detect_async(
                    mp.Image(data=frame, image_format=mp.ImageFormat.SRGB),
                    timestamp_ms)
            else:
                self.frame = None
                self.hands = None
    
    def get_annotated_frame(self):
        if self.frame is None or self.hands is None:
            return None
        
        hand_landmarks_list = self.hands.hand_landmarks
        annotated_image = np.copy(self.frame)

        # Loop through the detected hands to visualize.
        for idx in range(len(hand_landmarks_list)):
            hand_landmarks = hand_landmarks_list[idx]

            # Draw the hand landmarks.
            hand_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
            hand_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in hand_landmarks
            ])
            solutions.drawing_utils.draw_landmarks(
            annotated_image,
            hand_landmarks_proto,
            solutions.hands.HAND_CONNECTIONS,
            solutions.drawing_styles.get_default_hand_landmarks_style(),
            solutions.drawing_styles.get_default_hand_connections_style())

        return annotated_image
    
    def hand_seen_within(self, period_ms: int):
        """
        Whether or not a hand was seen within `period_ms` of calling this function. When hands move
        quickly, there are occasional tracking hiccups. This method can be used to debounce a noisy
        hand presence signal.
        """
        if self.hands_last_seen_ms is None:
            return False
        
        return (time.get_ticks() - self.hands_last_seen_ms) < period_ms
    
    @staticmethod
    def create_hand_detector(root_dir: str, callback: Callable[[HandLandmarkerResult, mp.Image, int], None]) -> HandLandmarker:
        hand_landmarker_path = path.join(root_dir, "models/hand_landmarker.task")
        base_options = BaseOptions(model_asset_path=hand_landmarker_path, delegate=BaseOptions.Delegate.CPU)
        options = HandLandmarkerOptions(base_options=base_options,
                                            num_hands=2,
                                            running_mode=RunningMode.LIVE_STREAM,
                                            result_callback=callback)
        detector = HandLandmarker.create_from_options(options)
        return detector