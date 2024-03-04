import threading
import os
import sys
from queue import Queue
from .state import State
from ..camera import get_working_ports
import pygame
from pygame.surface import Surface
from pygame.event import Event
from cv2 import VideoCapture
import pygame_gui


class Setup(State):
    CAMERA_LIST_REFRESH_PERIOD_MS = 10000

    camera: VideoCapture | None
    camera_dropdown: pygame_gui.elements.UIDropDownMenu
    ui_manager: pygame_gui.UIManager

    def __init__(self):
        self.ms_since_cameras_scanned = 0 # This can exceed CAMERA_LIST_REFRESH_PERIOD_MS
        self.camera_ports = []
        self.camera_ports_queue = Queue()  # Thread-safe queue to hold the scanning results
        self.update_camera_ports()  # Start the initial scan in a background thread
        self.camera = None # Either None (no camera) or a cv2.VideoCapture of the target camera.
        self.ui_manager = pygame_gui.UIManager(pygame.display.get_window_size())
        self.camera_dropdown = Setup.make_camera_dropdown([], None, self.ui_manager)

    def update_camera_ports(self):
        """
        Starts the camera_scan_thread function in the background to avoid blocking.
        """
        thread = threading.Thread(target=self.camera_scan_thread)
        thread.daemon = True
        thread.start()

    def camera_scan_thread(self):
        """Work done to scan for cameras in the background thread. Blocking and slow."""
        working_ports = get_working_ports()
        self.camera_ports_queue.put(working_ports) # Communicate the results back

    def draw(self, screen: Surface):
        screen.fill("purple")

        self.ui_manager.draw_ui(screen)
        
        if self.camera:
            frame_exists, frame = self.camera.read()
            if frame_exists:
                frame = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")
                frame = pygame.transform.scale(frame, (200, 100))
                screen.blit(frame, (400, 400))
    
    def update(self, delta: int):
        # We only attempt to refresh the camera list in the gametick that straddles the refresh period.
        # This is very important, because the camera refresh happens in the background - failing
        # to debounce would produce many refresh threads.
        should_refresh_cameras = self.ms_since_cameras_scanned <= self.CAMERA_LIST_REFRESH_PERIOD_MS \
                     and delta + self.ms_since_cameras_scanned > self.CAMERA_LIST_REFRESH_PERIOD_MS

        # Refresh the camera list if needed
        if should_refresh_cameras:
            self.update_camera_ports()
        
        self.ms_since_cameras_scanned += delta
        
        # Update camera_ports if the background thread has finished scanning
        if not self.camera_ports_queue.empty():
            self.camera_ports = self.camera_ports_queue.get()
            self.ms_since_cameras_scanned = 0  # Reset the scanning timer here
            
            old_selection = self.get_selected_port()

            # Rebuild the dropdown. This will be jarring to the user if we don't also preserve the
            # dropdown's expansion state
            was_expanded = self.camera_dropdown.current_state == self.camera_dropdown.menu_states['expanded']
            self.camera_dropdown.kill()
            self.camera_dropdown = Setup.make_camera_dropdown(self.camera_ports, old_selection, self.ui_manager)
            if was_expanded:
                self.camera_dropdown.current_state.finish()
                self.camera_dropdown.current_state = self.camera_dropdown.menu_states['expanded']
                self.camera_dropdown.current_state.start(should_rebuild=True)

                # The expanded state closes on the focus -> defocus transition. This breaks unless we also
                # replicate the focus state
                self.ui_manager.set_focus_set(self.camera_dropdown)
            
            # If the dropdown menu was unable to preserve our old selection (i.e. the chosen option is gone),
            # we need to make the selected camera correspond.
            new_selection = self.get_selected_port()
            if old_selection != new_selection:
                self.set_camera(new_selection)
        
        self.ui_manager.update(delta / 1000)

    def handle_event(self, event: Event):
        # Give the ui manager a chance to consume this event
        if self.ui_manager.process_events(event):
            return

        # Otherwise, it's for us :)
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.camera_dropdown:
                self.set_camera(self.get_selected_port())
                return
    
    def set_camera(self, port: int | None):
        if port is not None:
            self.camera = VideoCapture(port)
        else:
            self.camera = None
    
    def get_selected_port(self) -> int | None:
        selection = self.camera_dropdown.selected_option
        if selection == "No Cameras Found":
            return None
        else:
            return int(selection.split(' ')[-1])
    
    @staticmethod
    def make_camera_dropdown(ports: list[int], selection: int | None, ui_manager: pygame_gui.UIManager) -> pygame_gui.elements.UIDropDownMenu:
        if len(ports) == 0:
            options = ["No Cameras Found"]
            selection = options[0]
        else:
            options = [f"Camera {port}" for port in ports]

            # Try to preserve the selected option, if it still exists:
            if selection in ports:
                selection = f"Camera {selection}"
            else:
                selection = options[0]
        
        return pygame_gui.elements.UIDropDownMenu(
            options,
            selection,
            pygame.Rect((200, 200), (100,50)),
            ui_manager)
