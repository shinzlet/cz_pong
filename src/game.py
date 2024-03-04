import pygame
from .states.setup import Setup
from .tracking_context import TrackingContext
import mediapipe as mp

# from enum import Enum

# class GameState(Enum):
#     """
#     Represents each sufficiently isolated game state (i.e. states that clearly do not overlap. Changing
#     the game state will destroy the data of the state being exited).
#     """

#     SETUP = 0
#     """Corresponds to the setup menu where a user selects input devices and starts the game."""

#     PONG = 1
#     """Corresponds to the actual gameplay state. Note that a paused game is a substate of PONG - 
#     it is effectively an overlay, and the pong game is not dest"""

#     SCORING = 2
#     """Corresponds to the screen that shows the user their score in the previous game and highscores."""

class Game:
    tracking: TrackingContext
    
    def __init__(self, root_dir: str) -> None:
        pygame.init()
        self.root_dir = root_dir
        self.state = None
        self.tracking = TrackingContext(self.root_dir, None)

    def start(self):
        """Starts the gameloop. This method blocks until the user quits the game."""

        screen = pygame.display.set_mode((1280, 720))
        clock = pygame.time.Clock()
        running = True

        self.state = Setup(self.tracking)

        while running:
            # poll for events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.state.handle_event(event)


            self.state.draw(screen)

            delta = clock.tick(60)
            self.state.update(delta)

            # Tracking is async and has some latency in a different thread. Double buffering
            # is also a BIT slow, so there is likely less total motion-to-photon latency by
            # doing tracking at the end of the gameloop with the buffer flip than by tracking
            # before the draw & update (although the latter is more intuitive).
            self.tracking.update(pygame.time.get_ticks())

            # flip() the display to put your work on screen
            pygame.display.flip()


        pygame.quit()


if __name__ == "__main__":
    print("This is not the entry point of cz_pong. You likely meant to run `main.py`, not `src/game.py`.")
    exit(1)