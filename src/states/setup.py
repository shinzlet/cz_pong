import threading
import os
import sys
from queue import Queue
from .state import State
from ..camera import get_working_ports
from ..tracking_context import TrackingContext
from ..events import START_PONG
import pygame
from pygame.surface import Surface
from pygame.event import Event
from cv2 import VideoCapture
import pygame_gui


class Setup(State):
    CAMERA_LIST_REFRESH_PERIOD_MS = 10000
    START_WAIT_PERIOD_MS = 2000
    camera_dropdown: pygame_gui.elements.UIDropDownMenu
    ui_manager: pygame_gui.UIManager
    tracking: TrackingContext
    hand_visibility_duration_ms: int

    def __init__(self, tracking: TrackingContext):
        self.ms_since_cameras_scanned = self.CAMERA_LIST_REFRESH_PERIOD_MS - 1 # This can exceed CAMERA_LIST_REFRESH_PERIOD_MS
                                                                               # Set to cause a refresh in the first frame for 
                                                                               # less code duplication
        self.camera_ports = []
        self.camera_ports_queue = Queue()  # Thread-safe queue to hold the scanning results
        self.ui_manager = pygame_gui.UIManager(pygame.display.get_window_size())
        self.camera_dropdown = Setup.make_camera_dropdown([], None, self.ui_manager)
        self.tracking = tracking
        self.hand_visibility_duration_ms = 0 # If a hand is in view, how long it's been uninterruptedly shown.

    def draw(self, screen: Surface):
        screen.fill("purple")

        self.ui_manager.draw_ui(screen)
        
        # Display the camera image if one is present
        frame = self.tracking.frame
        if frame is not None:
            frame = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
            frame = pygame.transform.scale(frame, (200, 100))
            screen.blit(frame, (400, 400))
    
    def update(self, delta: int):
        self.update_camera_list(delta)
        self.sync_ui_to_camera_list()

        # If the user's hands have been in frame for long enough, transition from setup to
        # the main game:
        if self.tracking.hand_seen_within(300):
            self.hand_visibility_duration_ms += delta
        else:
            self.hand_visibility_duration_ms = 0
        
        if self.hand_visibility_duration_ms > self.START_WAIT_PERIOD_MS:
            pygame.event.post(pygame.event.Event(START_PONG))

        self.ui_manager.update(delta / 1000)
    
    def camera_scan_thread(self):
        """Work done to scan for cameras in the background thread. Blocking and slow."""
        working_ports = get_working_ports()
        self.camera_ports_queue.put(working_ports) # Communicate the results back

    def update_camera_list(self, delta: int):
        """
        Track the time since the available camera ports were last enumerated and dispatch a background
        task to update the list if needed.
        """
        # We only attempt to refresh the camera list in the gametick that straddles the refresh period.
        # This is very important, because the camera refresh happens in the background - failing
        # to debounce would produce many refresh threads.
        should_refresh_cameras = self.ms_since_cameras_scanned <= self.CAMERA_LIST_REFRESH_PERIOD_MS \
                     and delta + self.ms_since_cameras_scanned > self.CAMERA_LIST_REFRESH_PERIOD_MS

        # Refresh the camera list if needed
        if should_refresh_cameras:
            # Starts the camera_scan_thread function in the background to avoid blocking.
            thread = threading.Thread(target=self.camera_scan_thread)
            thread.daemon = True
            thread.start()
        
        self.ms_since_cameras_scanned += delta
    
    def sync_ui_to_camera_list(self):
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
            self.tracking.camera = VideoCapture(port)
        else:
            self.tracking.camera = None
    
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
