from typing import Tuple
import pygame
import numpy as np

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
