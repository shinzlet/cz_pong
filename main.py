from os import path
from src.game import Game

ROOT_DIR = path.dirname(path.abspath(__file__))

if __name__ == "__main__":
    Game(ROOT_DIR).start()