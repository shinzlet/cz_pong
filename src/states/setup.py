import threading
from typing import List
from queue import Queue
import pygame
from pygame.surface import Surface
from pygame.event import Event
from pygame.font import Font
import pygame_gui
from cv2 import VideoCapture
import numpy as np
import hsluv
from .state import State
from ..camera import get_working_ports
from ..tracking_context import TrackingContext
from ..events import START_PONG

class Setup(State):
    CAMERA_LIST_REFRESH_PERIOD_MS = 10000

    # How long the player's hand must be in frame for the pong game to start.
    START_WAIT_PERIOD_MS = 5000

    # How close UI elements can get to the window border (px)
    MARGIN = 50

    # The spacing between adjacent UI elements (px)
    GAP = 10

    # How long since the available cameras were polled. Note: this can exceed CAMERA_LIST_REFRESH_PERIOD_MS!
    ms_since_cameras_scanned: int

    # A list containing working camera ports that opencv can make a VideoCapture object from.
    camera_ports: List[int]

    # A thread-safe queue used to send `camera_ports` from the polling thread to the ui thread.
    camera_ports_queue: Queue
    ui_manager: pygame_gui.UIManager
    camera_dropdown: pygame_gui.elements.UIDropDownMenu
    tracking: TrackingContext

    # If a hand is in view, how long it's been uninterruptedly shown. Otherwise 0.
    hand_visibility_duration_ms: int

    font: Font

    def __init__(self, font: Font, tracking: TrackingContext):
        # Set to cause a refresh in the first frame for less code duplication
        self.ms_since_cameras_scanned = self.CAMERA_LIST_REFRESH_PERIOD_MS - 1
        self.camera_ports = []
        self.camera_ports_queue = Queue()
        self.ui_manager = pygame_gui.UIManager(pygame.display.get_window_size())
        self.camera_dropdown = Setup.make_camera_dropdown([], None, self.ui_manager)
        self.tracking = tracking
        self.hand_visibility_duration_ms = 0
        self.font = font

    def draw(self, screen: Surface):
        # The brightness of the setup screen "breathes" over time. It also becomes more saturated
        # and brighter while the user's hands are in frame, eventually turning white before the game
        # starts.
        time_s = pygame.time.get_ticks() / 1000
        start_proximity = self.hand_visibility_duration_ms / self.START_WAIT_PERIOD_MS
        
        hue = time_s * 20
        saturation = 10 + 150 * start_proximity
        luminosity = 10 + 10 * np.sin(time_s / 2) ** 8 + start_proximity * 80

        screen.fill(hsluv.hsluv_to_hex((hue, np.clip(saturation, 0, 100), luminosity)))

        # Renders the text and dropdown menu to the screen.
        # This layout code is a bit messy, but our UI needs are so simple that this is an easier approach
        # than fully digging into pygame_gui. For a more serious project, location anchors could be
        # used to automate relative positioning.
        x = self.MARGIN
        y = self.MARGIN
        text_surface, text_rect = self.font.render("Select a Camera", "white")
        screen.blit(text_surface, (x, y))

        y += self.GAP + text_rect.height
        text_surface, text_rect = self.font.render("(this list refreshes automatically)", "white")
        text_surface = pygame.transform.smoothscale_by(text_surface, 0.75)
        screen.blit(text_surface, (x, y))

        y += 4 * self.GAP
        self.camera_dropdown.set_position((x, y))

        if self.hand_visibility_duration_ms > 0:
            time_left = (self.START_WAIT_PERIOD_MS - self.hand_visibility_duration_ms) / 1000
            start_message = f"Hold for {time_left:.1f} seconds!"
        else:
            start_message = "Hold your hand in frame to start the game."
        
        text_surface, text_rect = self.font.render(start_message, "white")
        screen.blit(text_surface, (x, screen.get_height() - self.MARGIN - text_rect.height))

        # Draw the camera preview in the remaining unused space on the screen.
        min_x = self.camera_dropdown.get_abs_rect().right
        self.draw_camera_preview(screen, min_x)

        self.ui_manager.draw_ui(screen)

    def draw_camera_preview(self, screen, min_x: int) -> None:
        frame = self.tracking.get_annotated_frame()
        if frame is not None:
            frame = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "BGR")
            frame_width, frame_height = frame.get_size()
            aspect_ratio = frame_width / frame_height

            # Calculate available space considering minimum x and margin
            available_width = screen.get_width() - 2 * self.MARGIN - min_x
            available_height = screen.get_height() - 2 * self.MARGIN

            # Scale image within available space while maintaining aspect ratio
            if (available_width / aspect_ratio) <= available_height:
                new_width = available_width
                new_height = available_width / aspect_ratio
            else:
                new_width = available_height * aspect_ratio
                new_height = available_height

            # Scale the frame to the new dimensions
            frame = pygame.transform.scale(frame, (int(new_width), int(new_height)))

            # The frame by default looks like how a viewer would see you - not how you would look
            # in a mirror. We flip the image so that your right hand is on the right side of the
            # preview.
            frame = pygame.transform.flip(frame, True, False)

            # Calculate y position to vertically center the image
            y_position = (screen.get_height() - new_height) // 2

            screen.blit(frame, (min_x + self.MARGIN, int(y_position)))

    
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
        """
        Creates a VideoCapture object and configures the TrackingContext to use it, if the port exists.
        If the port is not provided, nothing happens.
        """
        if port is not None:
            self.tracking.camera = VideoCapture(port)
        else:
            self.tracking.camera = None
    
    def get_selected_port(self) -> int | None:
        """Returns the integer value of the camera port selected in the dropdown. If there is no selection, returns None."""
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
            pygame.Rect((50, 50), (250, 50)),
            ui_manager)
