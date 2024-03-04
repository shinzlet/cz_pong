from os import path
from typing import Callable
import mediapipe as mp
from mediapipe.tasks import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerResult, HandLandmarkerOptions, RunningMode

def create_hand_detector(root_dir: str, callback: Callable[[HandLandmarkerResult, mp.Image, int], None]) -> HandLandmarker | None:
    # TODO: Error handle when no model is found
    hand_landmarker_path = path.join(root_dir, "models/hand_landmarkerd.task")
    try:
        base_options = BaseOptions(model_asset_path=hand_landmarker_path, delegate=BaseOptions.Delegate.CPU)
        options = HandLandmarkerOptions(base_options=base_options,
                                            num_hands=2,
                                            running_mode=RunningMode.LIVE_STREAM,
                                            result_callback=callback)
        detector = HandLandmarker.create_from_options(options)
        return detector
    except FileNotFoundError:
        print(f"The hand landmarker model '{hand_landmarker_path}' was not found. Try making a fresh clone of this repo or opening an issue on GitHub for help.")
        return None
