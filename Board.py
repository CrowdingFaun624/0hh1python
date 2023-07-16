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
        self.__current_mouse_over:int = None
        self.get_board_from_seed()
        self.init_tiles()
        self.is_complete = False # used for locking all of the tiles

    def get_board_from_seed(self) -> list[int]:
        self.full_board, self.empty_board, self.other_data =  LevelCreator.generate(self.size, self.seed, self.colors)
        if self.colors == 2:
            self.player_board = self.empty_board[:]
        else:
            DEFAULT = list(range(1, self.colors + 1))
            self.player_board = [(DEFAULT[:] if value == 0 else [value]) for value in self.empty_board]

    def init_tiles(self) -> None:
        self.tiles:list[Tile.Tile] = []
        current_time = time.time()
        for index in range(self.size[0] * self.size[1]):
            x = index % self.size[0]
            y = index // self.size[0]
            is_even = (x + y) % 2 == 1
            if self.tile_is_empty(self.empty_board[index]):
                start_progress = 0.0
                is_locked = False
            else:
                start_progress = 1.0
                is_locked = True
            self.tiles.append(Tile.Tile(index, self.display_size, self.player_board[index], is_even, self.colors, current_time, start_progress, is_locked))

    def display(self, ticks:int) -> pygame.Surface:
        padding_amount = self.display_size * 0.04
        surface = pygame.Surface((self.display_size * self.size[0] + padding_amount, self.display_size * self.size[1] + padding_amount), pygame.SRCALPHA)
        current_time = time.time()
        for index in range(self.size[0] * self.size[1]):
            x = index % self.size[0]
            y = index // self.size[0]
            tile_surface_requirements = self.tiles[index].tick(current_time)
            tile_surface = self.tiles[index].display(tile_surface_requirements, current_time)
            self.tiles[index].last_tick_time = current_time
            surface.blit(tile_surface, (x*self.display_size, y*self.display_size))
        return surface

    def tile_is_empty(self, tile) -> bool:
        if tile == 0: return True
        elif isinstance(tile, list): return len(tile) == self.colors

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[int,int]) -> None:
        def get_relative_mouse_position(position:tuple[float,float]|None=None) -> tuple[float,float]:
            if position is None: position = event.__dict__["pos"]
            return position[0] - screen_position[0], position[1] - screen_position[1]
        def get_index(position:tuple[float,float]|None=None) -> int|None:
            '''Gets the index of the tile the mouse is over'''
            if position is None: position = event.__dict__["pos"]
            position = get_relative_mouse_position(position)
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
            self.tiles[index].click_time = time.time()
            if not self.tile_is_empty(self.empty_board[index]) or self.is_complete: # if it is a locked tile
                self.tiles[index].click_type = CLICK_ACTION_LOCKED
                return
            else: self.tiles[index].click_type = CLICK_ACTION_SUCCESS
            if self.colors == 2:
                current_value = self.player_board[index]
                self.tiles[index].previous_value = current_value
                current_value += up_values[event.__dict__["button"]]
                current_value = current_value % (self.colors + 1)
                self.player_board[index] = current_value
                self.tiles[index].value = current_value
                if 0 not in self.player_board: self.is_complete = True
            else:
                self.tiles[index].previous_value = self.player_board[index][:]
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
                        self.tiles[index].click_time_sections[section - 1] = time.time()
                else:
                    if section not in self.player_board[index]:
                        self.player_board[index].append(section)
                        self.tiles[index].click_time_sections[section - 1] = time.time()
                    for color in range(self.colors):
                        if color == section - 1: continue
                        if color + 1 in self.player_board[index]:
                            self.player_board[index].remove(color + 1)
                            self.tiles[index].click_time_sections[color] = time.time()
                if False not in [len(tile) == 1 for tile in self.player_board]: self.is_complete = True

        # def mouse_over() -> None:
        #     index = get_index(pygame.mouse.get_pos())
        #     if index is None: return
        def mouse_motion() -> None:
            index = get_index()
            if index is None:
                if self.__current_mouse_over is not None:
                    self.tiles[self.__current_mouse_over].is_mousing_over = False
                    self.__current_mouse_over = None
                return
            if index != self.__current_mouse_over:
                
                if self.__current_mouse_over is not None:
                    self.tiles[self.__current_mouse_over].mouse_over_time = time.time()
                    self.tiles[self.__current_mouse_over].is_mousing_over = False
                self.tiles[index].mouse_over_start = time.time() # NOTE: it might be worth considering setting the previous one back to 0
                self.tiles[index].is_mousing_over = True
            self.__current_mouse_over = index
        def mouse_leave() -> None:
            if self.__current_mouse_over is not None:
                self.tiles[self.__current_mouse_over].is_mousing_over = False
            self.__current_mouse_over = None
        
        TYPES = {
            pygame.MOUSEBUTTONDOWN: mouse_button_down,
            pygame.MOUSEMOTION: mouse_motion
        }
        for event in events:
            match event.type:
                case pygame.MOUSEBUTTONDOWN: mouse_button_down()
                case pygame.MOUSEMOTION: mouse_motion()
                case pygame.WINDOWLEAVE: mouse_leave()
            # if event.type in TYPES: TYPES[event.type]()
        # mouse_over()
