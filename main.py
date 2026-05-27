import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chess_game import Chess

if __name__ == "__main__":
    game = Chess()
    game.play()
