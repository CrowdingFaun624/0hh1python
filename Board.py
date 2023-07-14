import math
import pygame
import random
import time

import Drawable
import Utilities.LevelCreator as LevelCreator
import Buttons.Tile as Tile

CLICK_ACTION_LOCKED = "locked"
CLICK_ACTION_SUCCESS = "success"

class Board(Drawable.Drawable):

    def __init__(self, size:int|tuple[int,int], seed:int=None, colors:int=2) -> None:
        if isinstance(size, int): size = (size, size)
        largest_size = max(size)
        self.display_size = 640 / largest_size
        if seed is None: self.seed = random.randint(-2147483648, 2147483647)
        else:self.seed = seed
        self.size = size
        self.colors = colors
        if self.colors == 2:
            self.__click_times = [0] * (size[0] * size[1])
            self.__click_times_sections = [None] * (size[0] * size[1])
            self.__mouse_over_times = [0] * (size[0] * size[1])
            self.__click_types = [None] * (size[0] * size[1])
            self.__previous_tiles = [None] * (size[0] * size[1]) # keeps track of a tile's previous value
        else:
            DEFAULT = list(range(1, self.colors + 1))
            self.__click_times = [0] * (size[0] * size[1])
            self.__click_times_sections = [[0] * self.colors for i in range(size[0] * size[1])]
            self.__mouse_over_times = [0] * (size[0] * size[1])
            self.__click_types = [None] * (size[0] * size[1])
            self.__previous_tiles = [DEFAULT[:]] * (size[0] * size[1]) # keeps track of a tile's previous value
        self.get_board_from_seed()
        self.is_complete = False # used for locking all of the tiles

    def get_board_from_seed(self) -> list[int]:
        self.full_board, self.empty_board, self.other_data =  LevelCreator.generate(self.size, self.seed, self.colors)
        if self.colors == 2:
            self.player_board = self.empty_board[:]
        else:
            DEFAULT = list(range(1, self.colors + 1))
            self.player_board = [(DEFAULT[:] if value == 0 else [value]) for value in self.empty_board]

    def display(self, ticks:int) -> pygame.Surface:
        padding_amount = self.display_size * 0.04
        surface = pygame.Surface((self.display_size * self.size[0] + padding_amount, self.display_size * self.size[1] + padding_amount), pygame.SRCALPHA)
        board_data = {"colors": self.colors}
        for y in range(self.size[1]):
            for x in range(self.size[0]):
                index = x + y * self.size[0]
                is_even = (x + y) % 2 == 1
                tile_data = {
                    "click_time": self.__click_times[index],
                    "click_time_sections": self.__click_times_sections[index],
                    "mouse_over_time": self.__mouse_over_times[index],
                    "click_type": self.__click_types[index],
                    "previous_tile": self.__previous_tiles[index],
                    "locked": self.empty_board[index] != 0}
                # print(index)
                tile = Tile.Tile(self.display_size, self.player_board[index], is_even)
                surface.blit(tile.new_surface(ticks, time.time(), tile_data, board_data), (x*self.display_size, y*self.display_size))
        return surface

    def tile_is_empty(self, tile) -> bool:
        if tile == 0: return True
        elif isinstance(tile, list): return len(tile) == self.colors

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[int,int]) -> None:
        def get_relative_mouse_position() -> tuple[float,float]:
            return event.__dict__["pos"][0] - screen_position[0], event.__dict__["pos"][1] - screen_position[1]
        def get_index() -> int|None:
            '''Gets the index of the tile the mouse is over'''
            position = get_relative_mouse_position()
            if position[0] > self.display_size * self.size[0] or position[0] < 0: return None
            elif position[1] > self.display_size * self.size[1] or position[1] < 0: return None
            x = int(position[0] // self.display_size)
            y = int(position[1] // self.display_size)
            index = x + (self.size[0] * y)
            return index

        def mouse_button_down() -> None:
            up_values = {1: 1, 3: 2}
            if event.__dict__["button"] not in up_values: return
            index = get_index()
            if index is None: return
            self.__click_times[index] = time.time() 
            if not self.tile_is_empty(self.empty_board[index]) or self.is_complete: # if it is a locked tile
                self.__click_types[index] = CLICK_ACTION_LOCKED
                return
            else: self.__click_types[index] = CLICK_ACTION_SUCCESS
            if self.colors == 2:
                current_value = self.player_board[index]
                self.__previous_tiles[index] = current_value
                current_value += up_values[event.__dict__["button"]]
                current_value = current_value % (self.colors + 1)
                self.player_board[index] = current_value
                if 0 not in self.player_board: self.is_complete = True
            else:
                self.__previous_tiles[index] = self.player_board[index][:]
                x, y = get_relative_mouse_position()
                tile_x = index % self.size[0]; tile_y = index // self.size[0]
                center_x = (tile_x + 0.5) * self.display_size + screen_position[0]
                center_y = (tile_y + 0.5) * self.display_size + screen_position[1]
                direction = math.atan2(y - center_y, x - center_x) + (math.pi / 2) + (math.pi / self.colors) # in radians; clockwise; starts at left side and goes up; ends at 2pi
                section = (int(direction // (math.tau / self.colors)) % self.colors) + 1
                if event.__dict__["button"] != 3:
                    if section in self.player_board[index]:
                        self.player_board[index].remove(section)
                    else:
                        self.player_board[index].append(section)
                        self.player_board[index].sort() # so it is recognized correctly as DEFAULT
                    if self.tile_is_empty(self.empty_board[index]):
                        print("asdfasdf")
                        self.__click_times_sections[index][section - 1] = time.time()
                else:
                    if section not in self.player_board[index]:
                        self.player_board[index].append(section)
                        self.__click_times_sections[index][section - 1] = time.time()
                    # print("yeet")
                    for color in range(self.colors):
                        # print(color, color + 1, self.player_board[index])
                        if color == section - 1: continue
                        if color + 1 in self.player_board[index]:
                            self.player_board[index].remove(color + 1)
                            self.__click_times_sections[index][color] = time.time()
                # print(self.player_board[index])
                if False not in [len(tile) == 1 for tile in self.player_board]: self.is_complete = True

        def mouse_motion() -> None:
            index = get_index()
            if index is None: return
            self.__mouse_over_times[index] = time.time()
        
        TYPES = {
            pygame.MOUSEBUTTONDOWN: mouse_button_down,
            pygame.MOUSEMOTION: mouse_motion
        }
        for event in events:
            if event.type in TYPES: TYPES[event.type]()
