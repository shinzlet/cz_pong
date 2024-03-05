from os import path
import pygame
from pygame.freetype import Font
import mediapipe as mp
from .states import state as abstract_state, setup, pong
from .events import *
from .tracking_context import TrackingContext

class Game:
    tracking: TrackingContext
    
    # Constants for music playback
    SONG_PATH = 'assets/lofi-study.mp3'
    SONG_END_TIME_S = 75  # When to loop the song (in seconds)
    SONG_REPEAT_START_S = 6 # Where the song should restart after it reaches the end (in seconds)
    SONG_FADE_MS = 1500

    root_dir: str
    state: abstract_state.State
    tracking: TrackingContext
    song_playing: bool
    font: Font

    def __init__(self, root_dir: str) -> None:
        pygame.init()
        pygame.display.set_caption("seth hinz 4 instrumentation engineer")
        self.root_dir = root_dir
        self.state = None
        self.tracking = TrackingContext(self.root_dir, None)
        self.song_playing = False  # Track if the song is already playing
        self.font = Font(path.join(self.root_dir, "assets/MadimiOne-Regular.ttf"), 24)

    def play_music(self):
        """
        Begins the game music, if it is not already playing. Idempotent.
        """
        if not self.song_playing:
            pygame.mixer.music.load(f'{self.root_dir}/{self.SONG_PATH}')
            pygame.mixer.music.play(0)  # Loop indefinitely
            pygame.mixer.music.set_volume(0.3)
            self.song_playing = True

    def update_music(self):
        """
        Ensures the music loops seamlessly. Should be called every frame.
        """
        # Check the current playback position
        current_pos = pygame.mixer.music.get_pos() / 1000.0  # Convert milliseconds to seconds
        if current_pos >= self.SONG_END_TIME_S:
            # Cross-fade the music out and back in for good looping
            pygame.mixer.music.fadeout(self.SONG_FADE_MS)
            pygame.mixer.music.play(0, start=self.SONG_REPEAT_START_S, fade_ms=self.SONG_FADE_MS)
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.set_volume(1)  # Ensure volume is reset after fade

    def start(self):
        """Starts the gameloop. This method blocks until the user quits the game."""

        screen = pygame.display.set_mode((1280, 720))
        clock = pygame.time.Clock()
        running = True

        self.state = setup.Setup(self.font, self.tracking)

        while running:
            # poll for events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == START_PONG:
                    self.state = pong.Pong(self.root_dir, self.font, self.tracking)
                elif event.type == FIRST_HIT:
                    self.play_music() # For dramatic effect, there is no music until the player hits the ball
                elif event.type == GAME_OVER:
                    self.state = setup.Setup(self.font, self.tracking)
                else:
                    self.state.handle_event(event)

            self.update_music()

            self.state.draw(screen)

            delta = clock.tick(60)
            self.state.update(delta)

            # Tracking is async and has some latency in a different thread. Double buffering
            # is also a BIT slow, so there is likely less total motion-to-photon latency by
            # doing tracking at the end of the gameloop with the buffer flip than by tracking
            # before the draw & update (although the latter is more intuitive).
            self.tracking.update(pygame.time.get_ticks())

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    print("This is not the entry point of cz_pong. You likely meant to run `main.py`, not `src/game.py`.")
    exit(1)
