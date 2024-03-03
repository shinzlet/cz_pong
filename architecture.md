Upon starting the game, the player is put on a home screen where they can select a webcam. There is a preview window showing what the camera sees next to the webcam dropdown. Text is shown, saying the name of the game and prompting the user to raise the hand they want to use as a paddle into frame. Once a camera is selected, the user raises their preferred hand into view. After three seconds, this causes a tranisition to the tutorial game state. The hand used is recorded - the game will ignore the player's other hand. The hand (s) in the webcame frame are shown to the user while they are in the setup screen.

In the game, the user's hand elevation is mapped to the y coordinate of the paddle. The paddle is on the side of the screen that matches their dominant hand - i.e. left handed players see the paddle on the left side of the screen, and right handed players see the paddle on the right side of the screen. The background is either a solid color or a calm scrolling texture - the colors vary over time and as a function of the game state and score. The "front" direction points from the paddle towards the center of the screen - i.e. the direction the ball will travel when it moves away from the player. At the bottom of the screen there is a small information panel (score, total play time, dominant hand, and the sentence "to pause, remove your hand from view."). It is translucent, with white text on a soft black background. A lattice of translucent geometric shapes add texture to the game background, and by default they do not do anything.

To begin, a ball appears at the center of the screen. It drifts lazily in either a straight line or a seeking-curve towards the player's paddle. After the first hit, the game really starts - the player gets their first point, a sound effect plays, and the ball bounces towards the wall. Every time the ball hits the back wall, the ball's speed increases by some fixed additive amount. If the ball exits the screen on the paddle side, a sound plays and the game transitions to the scoring state.

If I have enough time, I want the game to include:
- angling of the paddle controlled by the player tilting their hand
- targets spawning on screen that, if hit by the ball, disappear and change the reactivity of the background
- color changes based on game state
- obstacles that glide along the screen to make the game more challenging.

The scoring state is a lot like the pause menu - the game statistics are shown on screen, alongside a "quit" and a "restart" button that are controlled by the player's hand as before. When this screen is reached, the player's score is saved in a highscore file.

The game pauses if the player's hands exit the frame. The pause menu has a resume and exit region, and the user must place their hand above one of these regions for 3 seconds to activate the corresponding game state.

Global state:
- Game state (Setup menu, Gameplay, Pause, Scoring screen)
- Webcam object
- Hand landmarker object
- Dominant hand
- Pygame objects
- Score results