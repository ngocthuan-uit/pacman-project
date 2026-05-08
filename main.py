"""
Entry point for Pacman Arcade.

Imports Game and calls run() to start the pygame event loop.
No game logic lives here; all initialisation is handled inside Game.__init__.
"""
from game import Game
 
if __name__ == "__main__":
    Game().run()