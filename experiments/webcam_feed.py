import cv2
import pygame
import sys
from pygame.locals import QUIT

# Initialize Pygame
pygame.init()

# Camera setup
cap = cv2.VideoCapture(0)  # 0 is typically the default camera
if not cap.isOpened():
    raise Exception("Could not open video device")

# Query the capture device for its width and height
ret, frame = cap.read()
height, width = frame.shape[:2]

# Pygame window setup
window_size = (width, height)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption('Camera Feed')

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which Pygame uses)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert the image to something Pygame can work with
    frame = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")

    # Display the image on the screen
    screen.blit(frame, (0, 0))

    # Update the display
    pygame.display.flip()

# When everything done, release the capture and close the windows
cap.release()
pygame.quit()
sys.exit()
