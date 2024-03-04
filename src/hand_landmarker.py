from os import path
import mediapipe as mp

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
HandLandmarkerResult = mp.tasks.vision.HandLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode
Delegate = mp.tasks.BaseOptions.Delegate

def create_hand_detector(root_dir: str) -> HandLandmarker | None:
    # TODO: Error handle when no model is found
    hand_landmarker_path = path.join(root_dir, "models/hand_landmarker.task")

    return None