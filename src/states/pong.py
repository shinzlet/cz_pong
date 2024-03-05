import hsluv
import numpy as np
import pygame
from os import path
from pygame import Surface, Event
from mediapipe.python.solutions.hands import HandLandmark
from .state import State
from ..events import FIRST_HIT, GAME_OVER
from ..tracking_context import TrackingContext
from ..ball import Ball

class Pong(State):
    PADDLE_WIDTH = 20
    PADDLE_HEIGHT = 100

    # The spacing of background decoration elements (i.e. the black circles). This is only approximately followed,
    # tweaks are made to fit the screen with a perfect tiling.
    BG_ACCENT_PITCH = 60

    # The maximum size of the black circles. Their actual size is modulated over time.
    BG_ACCENT_RADIUS = 20

    # The amount that the black circles wiggle around over time (this is a radius)
    BG_ACCENT_SWAY = 15

    BALL_MIN_SPEED = 150
    BALL_MAX_SPEED = 1000

    # The number of hits used as a time constant in the speed vs hits exponential.
    ACCELERATION_TIMESCALE = 10

    # How close text and decorations can come to the window border.
    BG_MARGIN = 30
    
    tracking: TrackingContext
    ball: Ball
    paddle_y: float
    background_hue: float
    score: int

    # This is a phase accumulator for some background animations. It increases monotonically with a derivative
    # equal to the ball's current speed (i.e. as gameplay quickens, decorations get faster too.)
    background_phase: float

    # The background hue changes at a constant speed, but otherwise is similar to the background phase. Purely aesthetic.
    background_hue: float

    hit_sound: pygame.mixer.Sound
    bounce_sound: pygame.mixer.Sound
    font: pygame.Font

    def __init__(self, root_dir: str, font: pygame.Font, tracking: TrackingContext):
        self.tracking = tracking
        self.ball = Ball(300, 200, 10, self.BALL_MIN_SPEED, -np.pi * 0.8, "white")
        self.paddle_y = pygame.display.get_surface().get_height() / 2
        self.score = 0
        self.background_phase = 0
        self.background_hue = 0
        self.hit_sound = pygame.mixer.Sound(path.join(root_dir, 'assets/flap.wav'))
        self.bounce_sound = pygame.mixer.Sound(path.join(root_dir, 'assets/knock.mp3'))
        self.bounce_sound.set_volume(0.8)
        self.font = font

    def draw(self, screen: Surface):
        # The background luminosity starts as 0 and goes to 100 as the ball speed reaches its max:
        normalized_ball_speed = (self.ball.speed - self.BALL_MIN_SPEED) / (self.BALL_MAX_SPEED - self.BALL_MIN_SPEED)
        bg_luminosity = normalized_ball_speed * 80

        # And the hue just increases over time.
        screen.fill(hsluv.hsluv_to_hex((self.background_hue, 100, bg_luminosity)))
        
        self.draw_background_accents(screen)

        # Render the score counter at the bottom right
        text_surface, text_rect = self.font.render(f"{self.score} hits", "white")
        screen.blit(text_surface, (self.BG_MARGIN, screen.get_height() - self.BG_MARGIN - text_rect.height))

        self.ball.draw(screen)
        
        # Draw the paddle
        pygame.draw.rect(
            screen,
            "white",
            self.paddle_rect())

    def update(self, delta: int):
        # Move the ball and react to wall hits and paddle hits:
        hit_paddle, hit_walls = self.ball.update(delta, self.arena_rect(), self.paddle_rect())

        if hit_paddle:
            # The first hit triggers the music to start playing for dramatic effect. :)
            if self.score == 0:
                pygame.event.post(pygame.event.Event(FIRST_HIT))
            
            self.score += 1
            speed_range = self.BALL_MAX_SPEED - self.BALL_MIN_SPEED
            # This is an easing function that exponentially interpolates between the min and max speed.
            # I made it just by tinkering around intuitively in desmos.
            self.ball.speed = self.BALL_MIN_SPEED + speed_range * (1 - np.exp(-self.score / self.ACCELERATION_TIMESCALE))
            self.hit_sound.play()
        
        if hit_walls:
            self.bounce_sound.play()
        
        # Steadily increase the hue:
        self.background_hue += delta / 100
        self.background_hue %= 360

        # Increase the background phase factor in proportion to the ball's step size (i.e. the decorations
        # move at a speed related to the ball's speed)
        self.background_phase += (self.ball.speed / self.BALL_MAX_SPEED) * (delta / 1000)
        self.background_phase %= 2 * np.pi

        self.track_paddle_to_hand()
        
        # If the ball is sufficiently far out of frame, end the game. This margin of 1.1x is used to make
        # the transition feel less shocking to the user - if we did this the instant the ball passed the paddle,
        # the user might not even see it go off screen!
        if self.ball.x > pygame.display.get_surface().get_width() * 1.1:
            pygame.event.post(pygame.event.Event(GAME_OVER))

    def handle_event(self, event: Event):
        pass

    def draw_background_accents(self, screen: Surface) -> None:
        # BG_ACCENT_PITCH is the target spacing between accents - but it rarely exactly divides
        # the background area. Here, we a pitch that is as close as possible to BG_ACCENT_PITCH
        # but that actually exactly divides the grid.
        full_margin = 2 * (self.BG_MARGIN + self.BG_ACCENT_RADIUS)
        w = screen.get_width() - full_margin
        h = screen.get_height() - full_margin

        x_count = w // self.BG_ACCENT_PITCH
        # The spacing between rows is less than the spacing between columns by cos(30º) because
        # we want to make a regular hexagonal (not a rectangular) grid
        y_count = h // int(self.BG_ACCENT_PITCH * np.cos(np.pi / 6))

        # This hexagonal tiling is only really well defined for grid sizes > 2x2. The default screen
        # size should never be this small, but we'd rather the game get uglier than have a divide by
        # zero error so we return early.
        if x_count <= 1 or y_count <= 1:
            return

        # If there are x_count circles spread over a width w (one circle on each boundary),
        # then there are x_count - 1 *gaps* between the posts.
        dx = w / (x_count - 1)
        dy = h / (y_count - 1)

        # The position of the top left circle.
        x0 = self.BG_MARGIN + self.BG_ACCENT_RADIUS
        y0 = x0

        # The decay constant used in the exponential falloff of the circle size modulation.
        # This was heuristally chosen to look good, there's no real reason this value is exactly
        # as it is.
        decay = 10 * self.ball.radius

        for i in range(x_count):
            for j in range(y_count):
                x = x0 + i * dx

                # Stagger the odd rows:
                if j % 2 == 0:
                    x -= dx / 2

                    # Staggered rows will fit one fewer dot in the permitted area.
                    if i == 0:
                        continue
                
                y = y0 + j * dy

                argument = 10 * i + j + self.background_phase
                x += self.BG_ACCENT_SWAY * np.cos(argument)
                y += self.BG_ACCENT_SWAY * np.sin(argument)

                # The radius changes with the distance to the ball to make the background "track"
                # it.
                ball_distance = np.hypot(x - self.ball.x, y - self.ball.y)
                r = self.BG_ACCENT_RADIUS * (0.1 + np.exp(-ball_distance / decay))
                pygame.draw.circle(screen, "black", (x, y), r)
    
    def track_paddle_to_hand(self) -> None:
        """
        Attempts to pin the paddle y position on the player's hand. If there is no hand tracking data, this has
        no effect.
        """
        if self.tracking.detection_result and len(self.tracking.detection_result.handedness) > 0:
            # Compute the y position of the center of the palm - roughly approximated by the
            # mean of the y position of the metacarpophalangeal joints of the pinky, index finger,
            # and the y position of the wrist:
            
            landmarks = self.tracking.detection_result.hand_landmarks[0]
            y = 0
            y += landmarks[HandLandmark.WRIST].y
            y += landmarks[HandLandmark.PINKY_MCP].y
            y += landmarks[HandLandmark.INDEX_FINGER_MCP].y
            y /= 3
            
            # y is normalized on [0, 1] - but detection is poor in the margins of the screen.
            # we clamp this to [0.2, 0.8] and then renormalize to ensure that the full control range
            # is reachable in the reliably detectable region of the view.
            y = np.clip(y, 0.2, 0.8)
            y = (y - 0.2) / 0.6
            self.paddle_y = y * (pygame.display.get_surface().get_height() - self.PADDLE_HEIGHT)

    def paddle_rect(self) -> pygame.rect.Rect:
        """Returns a rect representing the paddle on screen."""
        return pygame.rect.Rect(
            pygame.display.get_surface().get_width() - self.PADDLE_WIDTH,
            self.paddle_y,
            self.PADDLE_WIDTH,
            self.PADDLE_HEIGHT)

    def arena_rect(self) -> pygame.rect.Rect:
        """
        Returns the region of the screen where the ball is confined. Currently, this is the whole screen,
        but I had considered using a smaller region.
        """
        return pygame.display.get_surface().get_rect()
