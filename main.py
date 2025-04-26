import pygame
pygame.init()
from game_manager import GameManager


if __name__ == "__main__":
    game = GameManager(800, 600)
    game.run()
