from pygame.event import custom_type

# Dispatched from the Setup state when the game should start.
START_PONG = custom_type()

# Dispatched from teh Pong state when the user first hits the ball. This is used for aesthetics only (the music starts).
FIRST_HIT = custom_type()

# Dispatched when the ball leaves the pong game.
GAME_OVER = custom_type()