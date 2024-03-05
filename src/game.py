import pygame
from .states import setup, pong
from .tracking_context import TrackingContext
from .events import *
import mediapipe as mp
from os import path

class Game:
    tracking: TrackingContext
    
    # Constants for music playback
    SONG_PATH = 'assets/lofi-study.mp3'
    SONG_END_TIME_S = 75  # When to loop the song (in seconds)
    SONG_REPEAT_START_S = 6 # Where the song should restart after it reaches the end (in seconds)
    SONG_FADE_MS = 1500

    def __init__(self, root_dir: str) -> None:
        pygame.init()
        self.root_dir = root_dir
        self.state = None
        self.tracking = TrackingContext(self.root_dir, None)
        self.song_playing = False  # Track if the song is already playing
        self.font = pygame.freetype.Font(path.join(self.root_dir, "assets/MadimiOne-Regular.ttf"), 24)

    def play_music(self):
        if not self.song_playing:
            pygame.mixer.music.load(f'{self.root_dir}/{self.SONG_PATH}')
            pygame.mixer.music.play(0)  # Loop indefinitely
            pygame.mixer.music.set_volume(0.3)
            self.song_playing = True

    def update_music(self):
        # Check the current playback position
        current_pos = pygame.mixer.music.get_pos() / 1000.0  # Convert milliseconds to seconds
        if current_pos >= self.SONG_END_TIME_S:
            # Cross-fade the music out and back in for good looping
            pygame.mixer.music.fadeout(self.SONG_FADE_MS)
            pygame.mixer.music.play(0, start=self.SONG_REPEAT_START_S, fade_ms=self.SONG_FADE_MS)
            pygame.mixer.music.set_volume(1)  # Ensure volume is reset after fade

    def start(self):
        """Starts the gameloop. This method blocks until the user quits the game."""

        screen = pygame.display.set_mode((1280, 720))
        clock = pygame.time.Clock()
        running = True

        self.state = setup.Setup(self.tracking)

        while running:
            # poll for events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == START_PONG:
                    self.state = pong.Pong(self.root_dir, self.font, self.tracking)
                    self.play_music()  # Start playing the music when entering PONG state
                else:
                    self.state.handle_event(event)

            self.update_music()  # Update music playback state

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
