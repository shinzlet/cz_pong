import cv2
import random

# Currently, OpenCV does not have any sensible way to enumerate the available
# camera devices (https://github.com/opencv/opencv/issues/4269). The best we can do is
# enumerate over port indexes until we stop finding webcams - this method is adapted
# this stackoverflow answer: https://stackoverflow.com/a/62639343
def get_working_ports():
    """
    Tests camera ports and returns an array of working video capture device ports. This method is slow (~1s)
    and blocking.
    """

    print("Scanning for working camera ports. OpenCV will complain, but this is expected and an open issue")
    print("  (See https://github.com/opencv/opencv/issues/4269)")

    dev_port = 0
    dead_ports = 0
    working_ports = []
    while dead_ports < 2: # if there are more than 3 non working ports stop the testing. 
        camera = cv2.VideoCapture(dev_port)

        if not camera.isOpened():
            dead_ports += 1
        else:
            is_reading, img = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            if is_reading:
                working_ports.append(dev_port)
        
        camera.release()
        dev_port += 1
    
    return working_ports