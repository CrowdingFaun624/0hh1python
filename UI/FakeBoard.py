import time
from typing import Callable, Any

import pygame

import UI.Drawable as Drawable
import UI.Tile as Tile

class FakeBoard(Drawable.Drawable):
    def __init__(self, size:tuple[int,int], colors:int, contents:list[int|list[int]]|None, position:tuple[int,int], display_size:tuple[int,int]) -> None:
        self.size = size
        self.colors = colors
        if contents is None: contents = self.get_empty_contents()
        self.contents = contents
        self.display_size = display_size
        self.position = position
        super().__init__(None, position, [], self.get_tiles() + self.get_additional_children())
    
    def get_empty_contents(self, fill:int|list[int]|None=None) -> list[int|list[int]]:
        if fill is None:
            if self.colors == 2: fill = 0
            else:
                fill = list(range(1, self.colors + 1))
        return [fill] * (self.size[0] * self.size[1])

    def get_additional_children(self) -> list[Drawable.Drawable]:
        return []

    def set_position(self, new_position:tuple[int,int]) -> None:
        delta_x = new_position[0] - self.position[0]
        delta_y = new_position[1] - self.position[1]
        for child in self.children:
            child.position = (child.position[0] + delta_x, child.position[1] + delta_y)
        self.position = new_position

    def get_size(self) -> tuple[int,tuple[int,int]]:
        '''Returns the size per tile and the board's size.'''
        maximum_tile_width = int(self.display_size[0] / self.size[0])
        maximum_tile_height = int(self.display_size[1] / self.size[1])
        tile_size = min(maximum_tile_width, maximum_tile_height)
        return tile_size, (self.size[0] * tile_size, self.size[1] * tile_size)

    def get_tiles(self) -> list[Tile.Tile]:
        width, height = self.size
        current_time = time.time()
        tile_size, _ = self.get_size()
        self.tiles:list[Tile.Tile] = []
        for index in range(width * height):
            x = index % width # display position
            y = index // width
            is_even = (x + y) % 2 == 1
            start_progress = float(int(not self.tile_is_empty(self.contents[index])))
            tile = Tile.Tile(index, tile_size, self.contents[index], is_even, self.colors, current_time, start_progress, mode="static")
            tile.position = (self.position[0] + x * tile_size, self.position[1] + y * tile_size)
            self.tiles.append(tile)
        return self.tiles
    
    def tile_is_empty(self, tile:int|list[int]) -> bool:
        return (isinstance(tile, int) and tile == 0) or (isinstance(tile, list) and len(tile) == self.colors)
    
    def reload(self, current_time:float) -> None:
        self.children = self.get_tiles() + self.get_additional_children()
