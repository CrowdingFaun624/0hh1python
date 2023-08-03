import math
import random
import threading
import time

import pygame

import Buttons.Tile as Tile
import Colors
import Drawable
import Fonts.Fonts as Fonts
import Utilities.Bezier as Bezier
import Utilities.LevelCreator as LevelCreator
import Utilities.LevelPrinter as LevelPrinter

CLICK_ACTION_LOCKED = "locked"
CLICK_ACTION_SUCCESS = "success"
LOADING_TILE_SIZE = 0.5
FADE_IN_TIME = 0.3
FADE_OUT_TIME = 2.0
COMPLETION_WAIT_TIME = 0.75

class Board(Drawable.Drawable):

    def __init__(self, size:int|tuple[int,int], seed:int=None, colors:int=2, position:tuple[int,int]=(0,0), pixel_size:int=640, restore_objects:list[Drawable.Drawable]|None=None) -> None:
        if isinstance(size, int): size = (size, size)
        self.position = position
        self.should_destroy = False
        self.restore_objects = [] if restore_objects is None else restore_objects
        largest_size = max(size)
        self.display_size = pixel_size / largest_size
        if seed is None: self.seed = random.randint(-2147483648, 2147483647)
        else:self.seed = seed
        self.size = size
        self.colors = colors
        self.__current_mouse_over:int = None
        self.is_complete = False # used for locking all of the tiles
        self.is_fading_out = False
        self.is_finished_loading = False
        generation_thread = threading.Thread(target=self.get_board_from_seed)
        generation_thread.start()

    def loading_screen_init(self) -> None:
        self.loading_start_time = time.time()
        self.loading_finish_time = None
        self.completion_time = None
        padding_amount = self.display_size * 0.04
        loading_tile_size = LOADING_TILE_SIZE * min(self.display_size *  max(self.size) + padding_amount, self.display_size *  max(self.size) + padding_amount)
        self.loading_tile = Tile.Tile(0, loading_tile_size, self.colors, False, self.colors, self.loading_start_time)
        self.loading_tile.previous_value = None
        self.loading_text = Fonts.loading_screen.render("Loading", True, Colors.font)

    def get_board_from_seed(self) -> list[int]:
        self.loading_screen_init()
        self.full_board, self.empty_board, self.other_data, self.tiles = None, None, None, None
        # return
        self.full_board, self.empty_board, self.other_data = LevelCreator.generate(self.size, self.seed, self.colors)
        if self.colors == 2:
            self.player_board = self.empty_board[:]
        else:
            DEFAULT = list(range(1, self.colors + 1))
            self.player_board = [(DEFAULT[:] if value == 0 else [value]) for value in self.empty_board]
        self.init_tiles()
        
        self.is_finished_loading = True
        self.loading_finish_time = time.time()

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

    def display(self) -> pygame.Surface:
        padding_amount = self.display_size * 0.04
        if not self.is_finished_loading:
            largest_size = max(self.size)
            surface_size = (self.display_size * largest_size + padding_amount, self.display_size * largest_size + padding_amount)
        else:
            surface_size = (self.display_size * self.size[0] + padding_amount, self.display_size * self.size[1] + padding_amount)
        surface = pygame.Surface(surface_size, pygame.SRCALPHA)
        surface.fill(Colors.background)
        current_time = time.time()

        opacity = 1.0
        if self.loading_finish_time is not None:
            since_load_stop = current_time - self.loading_finish_time
            if since_load_stop <= FADE_IN_TIME:
                fraction_since_stop = since_load_stop / FADE_IN_TIME
                opacity = Bezier.ease_out(0.0, 1.0, fraction_since_stop)
        if self.is_fading_out:
            since_completion = current_time - self.completion_time - COMPLETION_WAIT_TIME
            if since_completion <= FADE_OUT_TIME:
                fraction_since_complete = since_completion / FADE_OUT_TIME
                opacity = 1 - Bezier.ease_in(0.0, 1.0, fraction_since_complete)
            else: opacity = 0.0

        if self.is_finished_loading:
            for index in range(self.size[0] * self.size[1]):
                x = index % self.size[0]
                y = index // self.size[0]
                tile_surface_requirements = self.tiles[index].tick(current_time)
                tile_surface = self.tiles[index].display(tile_surface_requirements, current_time)
                if opacity != 1.0: tile_surface.set_alpha(opacity * 255)
                elif tile_surface.get_alpha() != 255: tile_surface.set_alpha(255)
                
                self.tiles[index].last_tick_time = current_time
                surface.blit(tile_surface, (x*self.display_size, y*self.display_size))
            
        if not self.is_finished_loading or current_time - self.loading_finish_time <= FADE_IN_TIME:
            self.__display_loading_screen(current_time, surface_size, surface)
        return surface

    def __display_loading_screen(self, current_time:float, surface_size:tuple[float,float], surface:pygame.Surface) -> None:
        since_load_start = current_time - self.loading_start_time
        since_load_stop = current_time - self.loading_finish_time if self.loading_finish_time is not None else None
        opacity = 1.0
        if since_load_start < FADE_IN_TIME:
            fraction_since_start = since_load_start / FADE_IN_TIME
            opacity *= Bezier.ease_out(0.0, 1.0, fraction_since_start)
        if since_load_stop is not None and since_load_stop < FADE_IN_TIME:
            fraction_since_stop = since_load_stop / FADE_IN_TIME
            opacity *= 1 - Bezier.ease_out(0.0, 1.0, fraction_since_stop)
        if since_load_stop is not None and since_load_stop >= FADE_IN_TIME: opacity = 0.0

        center_x = surface_size[0] / 2; center_y = surface_size[1] * 1.25 / 2
        smallest_size = min(surface_size)
        tile_size = smallest_size * LOADING_TILE_SIZE
        corner_x_tile = center_x - (tile_size / 2); corner_y_tile = center_y - (tile_size / 2)
        loading_tile_surface = self.loading_tile.display_loading(current_time - self.loading_start_time)
        if opacity != 1.0: loading_tile_surface.set_alpha(opacity * 255)
        surface.blit(loading_tile_surface, (corner_x_tile, corner_y_tile))

        center_x = surface_size[0] / 2; center_y = surface_size[1] * 0.5 / 2
        text_size = self.loading_text.get_size()
        corner_x_text = center_x - (text_size[0] / 2); corner_y_text = center_y - (text_size[1] / 2)
        if opacity != 1.0: self.loading_text.set_alpha(opacity * 255)
        surface.blit(self.loading_text, (corner_x_text, corner_y_text))

    def tile_is_empty(self, tile) -> bool:
        if tile == 0: return True
        elif isinstance(tile, list): return len(tile) == self.colors

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[int,int]) -> None:
        def get_relative_mouse_position(position:tuple[float,float]|None=None) -> tuple[float,float]:
            if position is None: position = event.__dict__["pos"]
            return position[0] - screen_position[0], position[1] - screen_position[1]
        def get_index(position:tuple[float,float]|None=None) -> int|None:
            '''Gets the index of the tile the mouse is over'''
            if not self.is_finished_loading: return None
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
                if 0 not in self.player_board: self.is_complete = True; self.completion_time = time.time()
            else:
                self.tiles[index].previous_value = self.player_board[index][:]
                x, y = get_relative_mouse_position()
                tile_x = index % self.size[0]; tile_y = index // self.size[0]
                center_x = (tile_x + 0.5) * self.display_size
                center_y = (tile_y + 0.5) * self.display_size
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
                if False not in [len(tile) == 1 for tile in self.player_board]: self.is_complete = True; self.completion_time = time.time()

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
        
        if self.tiles is not None and len(self.tiles) != self.size[0] * self.size[1]: print("whoops! not fully constructed.")
        current_time = time.time()
        if self.is_complete: self.is_fading_out = (current_time - self.completion_time > COMPLETION_WAIT_TIME)
        if self.is_fading_out and current_time - self.completion_time > COMPLETION_WAIT_TIME + FADE_OUT_TIME:
            self.should_destroy = True
