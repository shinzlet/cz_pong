from .state import State
from ..events import FIRST_HIT, GAME_OVER
from ..tracking_context import TrackingContext
from pygame import Surface, Event
import hsluv
import pygame
from typing import Tuple

from os import path
import numpy as np
from mediapipe.python.solutions.hands import HandLandmark

class Pong(State):
    PADDLE_WIDTH = 20
    PADDLE_HEIGHT = 100
    BG_ACCENT_PITCH = 60
    BG_ACCENT_RADIUS = 20
    BG_ACCENT_SWAY = 15
    BALL_MIN_SPEED = 150
    BALL_MAX_SPEED = 1000
    ACCELERATION_TIMESCALE = 10 # The number of hits used as a time constant in the speed vs hits exponential.
    BG_MARGIN = 30
    
    tracking: TrackingContext
    background_hue: float

    def __init__(self, root_dir: str, font: pygame.Font, tracking: TrackingContext):
        self.tracking = tracking
        self.ball = Ball(300, 200, 10, self.BALL_MIN_SPEED, -np.pi * 0.8, "white")
        self.paddle_y = pygame.display.get_surface().get_height() / 2
        self.background_hue = 0
        self.score = 0
        self.background_phase = 0
        self.hit_sound = pygame.mixer.Sound(path.join(root_dir, 'assets/flap.wav'))
        self.bounce_sound = pygame.mixer.Sound(path.join(root_dir, 'assets/knock.mp3'))
        self.bounce_sound.set_volume(0.8)
        self.font = font

    def draw(self, screen: Surface):
        normalized_ball_speed = (self.ball.speed - self.BALL_MIN_SPEED) / (self.BALL_MAX_SPEED - self.BALL_MIN_SPEED)
        bg_luminosity = normalized_ball_speed * 80
        screen.fill(np.array(hsluv.hsluv_to_rgb((self.background_hue, 100, bg_luminosity))) * 255)
        
        self.draw_background(screen)

        text_surface, text_rect = self.font.render(f"{self.score} hits", "white")
        screen.blit(text_surface, (self.BG_MARGIN, screen.get_height() - self.BG_MARGIN - text_rect.height))

        self.ball.draw(screen)
        
        pygame.draw.rect(
            screen,
            "white",
            self.paddle_rect())

    def update(self, delta: int):
        hit_paddle, hit_walls = self.ball.update(delta, self.arena_rect(), self.paddle_rect())

        if hit_paddle:
            if self.score == 0:
                pygame.event.post(pygame.event.Event(FIRST_HIT))
            
            self.score += 1
            speed_range = self.BALL_MAX_SPEED - self.BALL_MIN_SPEED
            self.ball.speed = self.BALL_MIN_SPEED + speed_range * (1 - np.exp(-self.score / self.ACCELERATION_TIMESCALE))
            self.hit_sound.play()
        
        if hit_walls:
            self.bounce_sound.play()
        
        self.background_hue += delta / 100
        self.background_hue %= 360

        self.background_phase += (self.ball.speed / self.BALL_MAX_SPEED) * (delta / 1000)
        self.background_phase %= 2 * np.pi

        if self.tracking.hands and len(self.tracking.hands.handedness) > 0:
            # Compute the y position of the center of the palm - roughly approximated by the
            # mean of the y position of the metacarpophalangeal joints of the pinky, index finger,
            # and the y position of the wrist:
            
            landmarks = self.tracking.hands.hand_landmarks[0]
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
        
        if self.ball.x > pygame.display.get_surface().get_width() * 1.1:
            pygame.event.post(pygame.event.Event(GAME_OVER))

    def handle_event(self, event: Event):
        pass

    def draw_background(self, screen: Surface):
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

        if x_count <= 1 or y_count <= 1:
            return

        dx = w / (x_count - 1)
        dy = h / (y_count - 1)

        x0 = self.BG_MARGIN + self.BG_ACCENT_RADIUS
        y0 = x0

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
    
    def paddle_rect(self) -> pygame.rect.Rect:
        return pygame.rect.Rect(
            pygame.display.get_surface().get_width() - self.PADDLE_WIDTH,
            self.paddle_y,
            self.PADDLE_WIDTH,
            self.PADDLE_HEIGHT)

    def arena_rect(self) -> pygame.rect.Rect:
        return pygame.display.get_surface().get_rect()

class Ball:
    def __init__(self, x, y, radius, speed, angle, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.color = color
        self.direction = np.array([np.cos(angle), np.sin(angle)])

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

    def update(self, delta_ms, screen_rect, paddle_rect) -> Tuple[bool, bool]:
        # Calculate new position based on speed, direction, and delta time
        movement = self.direction * self.speed * delta_ms / 1000.0
        self.x += movement[0]
        self.y += movement[1]
        hit_paddle = False
        hit_wall = False

        # Create a rect for the ball to use for collision detection
        ball_rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)

        # Check for collision with the paddle
        if ball_rect.colliderect(paddle_rect):
            # Reflect the horizontal direction
            self.direction[0] *= -1
            # Adjust position to prevent sticking
            if self.x > screen_rect.width / 2:  # Assuming the paddle is on the right
                self.x = paddle_rect.left - self.radius - 1
            else:
                self.x = paddle_rect.right + self.radius + 1
            
            hit_paddle = True

        # Bounce off top and bottom
        if ball_rect.top <= screen_rect.top:
            self.direction[1] *= -1
            self.y = screen_rect.top + self.radius + 1
            hit_wall = True
        
        if ball_rect.bottom >= screen_rect.bottom:
            self.direction[1] *= -1
            self.y = screen_rect.bottom - self.radius - 1
            hit_wall = True

        # Bounce off the left (or right, if you want to change it, invert the logic here)
        if ball_rect.left <= screen_rect.left:  # Change to `ball_rect.right >= screen_rect.right` for right-side bounce
            self.direction[0] *= -1
            self.x = screen_rect.left + self.radius + 1
            hit_wall = True

        return (hit_paddle, hit_wall)
