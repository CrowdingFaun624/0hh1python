import math
import random
import threading
import time

import pygame

import LevelCreator.LevelCreator as LevelCreator
import LevelCreator.LevelHinter as LevelHinter
import LevelCreator.LevelUtilities as LU
import UI.Button as Button
import UI.Colors as Colors
import UI.Drawable as Drawable
import UI.Fonts as Fonts
import UI.Textures as Textures
import UI.Tile as Tile
import Utilities.Animation as Animation
import Utilities.Bezier as Bezier

CLICK_ACTION_LOCKED = "locked"
CLICK_ACTION_SUCCESS = "success"
LOADING_TILE_SIZE = 0.5
BOARD_FADE_IN_TIME = 0.3
BOARD_FADE_OUT_TIME_CLOSE = 0.1
BOARD_FADE_OUT_TIME_COMPLETE = 2.0
COMPLETION_WAIT_TIME = 0.75
LOADING_FADE_IN_TIME = 0.3
LOADING_FADE_OUT_TIME = 0.3

class Board(Drawable.Drawable):

    def __init__(self, size:int|tuple[int,int], seed:int=None, colors:int=2, position:tuple[int,int]=(0,0), pixel_size:int=640, restore_objects:list[Drawable.Drawable]|None=None, window_size:tuple[int,int]=None) -> None:
        if isinstance(size, int): size = (size, size)
        self.position = position
        self.should_destroy = False
        self.restore_objects = [] if restore_objects is None else restore_objects
        largest_size = max(size)
        self.pixel_size = pixel_size
        self.display_size = pixel_size / largest_size
        if seed is None: self.seed = random.randint(-2147483648, 2147483647)
        else:self.seed = seed
        self.size = size
        self.colors = colors

        self.__current_mouse_over:int = None
        self.show_locks = False # TODO: make this carry over between board instances.
        self.is_complete = False # used for locking all of the tiles
        self.board_opacity = Animation.Animation(0.0, 0.0, BOARD_FADE_IN_TIME, Bezier.ease_in)
        self.loading_opacity = Animation.Animation(1.0, 0.0, LOADING_FADE_IN_TIME, Bezier.ease_in)
        self.is_finished_loading = False
        self.window_size = window_size
        self.buttons = []
        self.hint_tiles:list[int] = []
        self.is_hinting = False
        self.history:list[tuple[int,int|list[int],int|list[int]]] = []
        # self.history is (index, value_set_to, previous_value)
        self.player_board_is_full = False
        self.player_board_fill_time = None
        self.marked_as_complete = False

        self.loading_screen_init()
        generation_thread = threading.Thread(target=self.get_board_from_seed)
        generation_thread.start()
        self.summoned_buttons = False

    def loading_screen_init(self) -> None:
        self.loading_start_time = time.time()
        padding_amount = self.display_size * 0.04
        loading_tile_size = LOADING_TILE_SIZE * min(self.display_size *  max(self.size) + padding_amount, self.display_size *  max(self.size) + padding_amount)
        self.loading_tile = Tile.Tile(0, loading_tile_size, self.colors, False, 2, self.loading_opacity.get())
        self.loading_tile.previous_value = None
        self.loading_text = Fonts.loading_screen.render("Loading", True, Colors.font)

    def get_board_from_seed(self) -> list[int]:
        self.full_board, self.empty_board, self.other_data, self.tiles = None, None, None, None
        # return
        self.full_board, self.empty_board, self.other_data = LevelCreator.generate(self.size, self.seed, self.colors, True)
        if self.colors == 2:
            self.player_board = self.empty_board[:]
        else:
            DEFAULT = list(range(1, self.colors + 1))
            self.player_board = [(DEFAULT[:] if value == 0 else [value]) for value in self.empty_board]
        self.init_tiles()
        
        self.loading_opacity.set(0.0, LOADING_FADE_OUT_TIME)
        self.board_opacity.set(1.0, BOARD_FADE_IN_TIME)
        self.is_finished_loading = True

    def get_lock_surface(self) -> pygame.Surface:
        '''Returns a copy of the lock texture, sized and opacitized correctly.'''
        lock_texture = Textures.textures["lock.png"]
        lock_size = 0.4 * self.display_size
        lock_surface = pygame.transform.scale(lock_texture, (lock_size, lock_size))
        lock_surface.set_alpha(51) # 0.2 * 255
        return lock_surface

    def init_tiles(self) -> None:
        self.tiles:list[Tile.Tile] = []
        current_time = time.time()
        lock_surface = self.get_lock_surface()
        for index in range(self.size[0] * self.size[1]):
            x = index % self.size[0]
            y = index // self.size[0]
            is_even = (x + y) % 2 == 1
            if self.tile_is_empty(self.empty_board[index]):
                start_progress = 0.0
                can_modify = True
                is_locked = False
            else:
                start_progress = 1.0
                can_modify = False
                is_locked = True
            self.tiles.append(Tile.Tile(index, self.display_size, self.player_board[index], is_even, self.colors, current_time, start_progress, is_locked, can_modify, self.show_locks, lock_surface))

    def display(self) -> pygame.Surface:
        padding_amount = self.display_size * 0.04
        if not self.is_finished_loading:
            largest_size = max(self.size)
            surface_size = (self.display_size * largest_size + padding_amount, self.display_size * largest_size + padding_amount)
        else:
            surface_size = (self.display_size * self.size[0] + padding_amount, self.display_size * self.size[1] + padding_amount)

        current_time = time.time()
        board_opacity = self.board_opacity.get(current_time)
        surface = pygame.Surface(surface_size, pygame.SRCALPHA)
        # surface.set_alpha(board_opacity * 255)
        for button in self.buttons: button.surface.set_alpha(board_opacity * 255)
        surface.fill(Colors.background)

        if self.is_finished_loading:
            for index in range(self.size[0] * self.size[1]):
                x = index % self.size[0]
                y = index // self.size[0]
                tile_surface_requirements = self.tiles[index].tick(current_time)
                tile_surface = self.tiles[index].display(tile_surface_requirements, current_time)
                tile_surface.set_alpha(board_opacity * 255)
                
                self.tiles[index].last_tick_time = current_time
                surface.blit(tile_surface, (x*self.display_size, y*self.display_size))
        
        loading_opacity = self.loading_opacity.get(current_time)
        if loading_opacity != 0.0:
            self.__display_loading_screen(current_time, surface_size, surface, loading_opacity)
        return surface

    def __display_loading_screen(self, current_time:float, surface_size:tuple[float,float], surface:pygame.Surface, opacity:float) -> None:
        center_x = surface_size[0] / 2; center_y = surface_size[1] * 1.25 / 2
        smallest_size = min(surface_size)
        tile_size = smallest_size * LOADING_TILE_SIZE
        corner_x_tile = center_x - (tile_size / 2); corner_y_tile = center_y - (tile_size / 2)
        loading_tile_surface = self.loading_tile.display_loading(current_time - self.loading_start_time)
        loading_tile_surface.set_alpha(opacity * 255)
        surface.blit(loading_tile_surface, (corner_x_tile, corner_y_tile))

        center_x = surface_size[0] / 2; center_y = surface_size[1] * 0.5 / 2
        text_size = self.loading_text.get_size()
        corner_x_text = center_x - (text_size[0] / 2); corner_y_text = center_y - (text_size[1] / 2)
        self.loading_text.set_alpha(opacity * 255)
        surface.blit(self.loading_text, (corner_x_text, corner_y_text))

    def tile_is_empty(self, tile) -> bool:
        if tile == 0: return True
        elif isinstance(tile, list): return len(tile) == self.colors
    
    def highlight(self, tiles_indexes:list[int]) -> None:
        self.is_hinting = True
        current_time = time.time()
        for tile_index in tiles_indexes:
            if not self.tiles[tile_index].is_highlighted:
                self.tiles[tile_index].highlight(current_time)
    def unhighlight(self) -> None:
        self.is_hinting = False
        for tile in self.tiles:
            tile.unhighlight()

    def update_locks(self) -> None:
        '''Will show/hide locks on tiles that were in the starting board.'''
        for index, tile in enumerate(self.empty_board):
            if self.tiles[index].is_locked:
                self.tiles[index].show_lock = self.show_locks

    def mark_as_complete(self) -> None:
        self.marked_as_complete = True
        self.unhighlight()
        expanded_player_board = LU.expand_board(self.colors, self.player_board) if isinstance(self.player_board[0], int) else self.player_board
        expanded_full_board = LU.expand_board(self.colors, self.full_board) if isinstance(self.full_board[0], int) else self.full_board
        if LU.boards_match(expanded_player_board, expanded_full_board):
            self.board_opacity.set(0.0, BOARD_FADE_OUT_TIME_COMPLETE)
            for button in self.buttons: button.enabled = False
            for tile in self.tiles:
                tile.can_modify = False
        else:
            tile_indexes = LU.get_not_matching_tiles(expanded_player_board, expanded_full_board)
            self.highlight(tile_indexes)

    def button_close(self) -> None:
        self.board_opacity.set(0.0, BOARD_FADE_OUT_TIME_CLOSE)
        for button in self.buttons: button.enabled = False
        for tile in self.tiles:
            tile.can_modify = False

    def button_undo(self) -> None:
        if len(self.history) == 0: return
        self.unhighlight()
        index, post, pre = self.history.pop()
        if self.colors == 2:
            self.player_board[index] = pre
            self.tiles[index].set_value(pre)
        else:
            for color in post:
                if color not in pre:
                    self.tiles[index].set_value_multi(color, False)
            for color in pre:
                if color not in post:
                    self.tiles[index].set_value_multi(color, True)
        self.tiles[index].highlight(time.time())

    def button_hint(self) -> None:
        if self.is_hinting:
            self.unhighlight()
        else:
            self.unhighlight()
            hint = LevelHinter.get_hint(self.size, self.colors, self.player_board, self.full_board)
            tile_indexes = hint.tiles_affected
            if isinstance(hint.target_tile, int): tile_indexes.append(hint.target_tile)
            self.highlight(tile_indexes)

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[int,int]) -> list[tuple[Drawable.Drawable]]|None:
        def get_relative_mouse_position(position:tuple[float,float]|None=None) -> tuple[float,float]:
            if position is None: position = event.__dict__["pos"]
            return position[0] - screen_position[0], position[1] - screen_position[1]
        def get_index(position:tuple[float,float]|None=None) -> int|None:
            '''Gets the index of the tile the mouse is over'''
            if not self.is_finished_loading: return None
            if position is None: position = event.__dict__["pos"]
            position = get_relative_mouse_position(position)
            if position[0] >= self.display_size * self.size[0] or position[0] <= 0: return None
            elif position[1] >= self.display_size * self.size[1] or position[1] <= 0: return None
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
            if not self.tiles[index].can_modify: # if it is a locked tile
                self.tiles[index].click_type = CLICK_ACTION_LOCKED
                if not self.is_complete and self.tiles[index].is_locked:
                    self.show_locks = not self.show_locks
                    self.update_locks()
                return
            else: self.tiles[index].click_type = CLICK_ACTION_SUCCESS
            if self.colors == 2:
                current_value = self.player_board[index]
                self.tiles[index].previous_value = current_value
                next_value = current_value + up_values[event.__dict__["button"]]
                next_value = next_value % (self.colors + 1)
                self.player_board[index] = next_value
                self.tiles[index].set_value(next_value)
                self.history.append((index, next_value, current_value))
                self.unhighlight()
                self.player_board_is_full = 0 not in self.player_board
            else:
                previous_value = self.player_board[index][:]
                self.tiles[index].previous_value = previous_value
                x, y = get_relative_mouse_position()
                tile_x = index % self.size[0]; tile_y = index // self.size[0]
                center_x = (tile_x + 0.5) * self.display_size
                center_y = (tile_y + 0.5) * self.display_size
                direction = math.atan2(y - center_y, x - center_x) + (math.pi / 2) + (math.pi / self.colors) # in radians; clockwise; starts at left side and goes up; ends at 2pi
                section = (int(direction // (math.tau / self.colors)) % self.colors) + 1
                self.unhighlight()
                if not self.tiles[index].can_modify: return
                if event.__dict__["button"] != 3:
                    self.tiles[index].set_value_multi(section, section not in self.player_board[index])
                else:
                    if section not in self.player_board[index]:
                        self.tiles[index].set_value_multi(section, True)
                    for color in range(self.colors):
                        if color == section - 1: continue
                        if color + 1 in self.player_board[index]:
                            self.tiles[index].set_value_multi(color + 1, False)
                self.player_board_is_full = False not in [len(tile) == 1 for tile in self.player_board]
                self.history.append((index, self.player_board[index][:], previous_value))
            if self.player_board_is_full: self.player_board_fill_time = time.time()
            self.marked_as_complete = False

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
                if index >= len(self.tiles): raise IndexError("list index (%i) out of range of %s" % (index, str(self.tiles)))
                self.tiles[index].mouse_over_start = time.time() # NOTE: it might be worth considering setting the previous one back to 0
                self.tiles[index].is_mousing_over = True
            self.__current_mouse_over = index
        def mouse_leave() -> None:
            if self.__current_mouse_over is not None:
                self.tiles[self.__current_mouse_over].is_mousing_over = False
            self.__current_mouse_over = None
        
        for event in events:
            match event.type:
                case pygame.MOUSEBUTTONDOWN: mouse_button_down()
                case pygame.MOUSEMOTION: mouse_motion()
                case pygame.WINDOWLEAVE: mouse_leave()
        
        current_time = time.time()
        # if self.is_complete: self.is_fading_out = (current_time - self.completion_time > COMPLETION_WAIT_TIME)
        # if self.is_fading_out and current_time - self.completion_time > COMPLETION_WAIT_TIME + BOARD_FADE_OUT_TIME_COMPLETE:
        if self.is_finished_loading and self.board_opacity.is_finished() and self.board_opacity.get(current_time) == 0.0:
            self.should_destroy = True
            for button in self.buttons:
                button.should_destroy = True
        # elif self.is_closing and current_time - self.close_time > BOARD_FADE_OUT_TIME_CLOSE:
        #     self.should_destroy = True
        #     for button in self.buttons:
        #         button.should_destroy = True
        def scale_texture(surface:pygame.Surface) -> pygame.Surface:
            return pygame.transform.scale_by(surface, self.window_size[1] / 900)
        # if self.player_board_fill_time is not None: print(current_time - self.player_board_fill_time)
        if self.player_board_is_full and not self.marked_as_complete and current_time - self.player_board_fill_time >= COMPLETION_WAIT_TIME:
            self.mark_as_complete()
        if self.is_finished_loading and not self.summoned_buttons:
            self.summoned_buttons = True
            buttons = [
                Button.Button(scale_texture(Textures.textures["close.png"]), screen_position, None, (self.button_close,)),
                Button.Button(scale_texture(Textures.textures["history.png"]), screen_position, None, (self.button_undo,)),
                Button.Button(scale_texture(Textures.textures["eye.png"]), screen_position, None, (self.button_hint,))
                ]

            sum_of_button_width = sum((button.surface.get_size()[0] for button in buttons))
            spacing = (self.pixel_size - sum_of_button_width) / (len(buttons) + 1)
            x = screen_position[0]
            for button in buttons:
                if self.window_size is None:
                    y = screen_position[1] + self.pixel_size + 12
                else:
                    y = int((screen_position[1] + self.pixel_size + self.window_size[1]) / 2 - button.surface.get_size()[1] / 2)
                x += spacing
                button.position = (x, y)
                x += button.surface.get_size()[0]

            self.buttons = buttons
            return [(button, 1) for button in self.buttons]
