import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# The absolute path of the hand landmarker model ('.task' file) that mediapipe will use.
HAND_LANDMARKER_PATH = os.path.join(PROJECT_ROOT, "models/hand_landmarker.task")

# STEP 2: Create an HandLandmarker object.
base_options = python.BaseOptions(model_asset_path=HAND_LANDMARKER_PATH)
options = vision.HandLandmarkerOptions(base_options=base_options,
                                       num_hands=2)
detector = vision.HandLandmarker.create_from_options(options)

# STEP 3: Load the input image.
image = mp.Image.create_from_file("image.jpg")

# STEP 4: Detect hand landmarks from the input image.
detection_result = detector.detect(image)
print(detection_result)

# STEP 5: Process the classification result. In this case, visualize it.
# annotated_image = draw_landmarks_on_image(image.numpy_view(), detection_result)
# cv2_imshow(cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))
