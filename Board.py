import pygame
import random

import Drawable
import Utilities.LevelCreator as LevelCreator
import Buttons.Tile as Tile

class Board(Drawable.Drawable):
    def __init__(self, size:int, seed:int=None) -> None:
        self.display_size = 640 / size
        if seed is None: self.seed = random.randint(-2147483648, 2147483647)
        else:self.seed = seed
        self.size = size
        self.get_board_from_seed()
    def get_board_from_seed(self) -> list[int]:
        self.full_board, self.empty_board, self.other_data =  LevelCreator.generate(self.size, self.seed)
    def display(self, ticks:int) -> pygame.Surface:
        padding_amount = self.display_size * 0.04
        surface = pygame.Surface((self.display_size * self.size + padding_amount, self.display_size * self.size + padding_amount), pygame.SRCALPHA)
        for y in range(self.size):
            for x in range(self.size):
                position = x + y * self.size
                is_even = (x + y) % 2 == 1
                tile = Tile.Tile(self.display_size, self.empty_board[position], is_even)
                surface.blit(tile.new_surface(ticks), (padding_amount + x*self.display_size, padding_amount + y*self.display_size))
        return surface
