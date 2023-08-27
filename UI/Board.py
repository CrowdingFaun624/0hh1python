import math
import threading
from typing import Any
import time

import pygame

import LevelCreator.LevelCreator as LevelCreator
import LevelCreator.LevelHinter as LevelHinter
import LevelCreator.LevelUtilities as LU
import UI.AxisCounter as AxisCounter
import UI.Button as Button
import UI.ButtonPanel as ButtonPanel
import UI.Colors as Colors
import UI.Drawable as Drawable
import UI.Fonts as Fonts
import UI.Textures as Textures
import UI.Tile as Tile
import Utilities.Animation as Animation
import Utilities.Bezier as Bezier
import Utilities.Settings as Settings

CLICK_ACTION_LOCKED = "locked"
CLICK_ACTION_SUCCESS = "success"
BOARD_FADE_IN_TIME = 0.1
BOARD_FADE_OUT_TIME_CLOSE = 0.1
BOARD_FADE_OUT_TIME_COMPLETE = 2.0
COMPLETION_WAIT_TIME = 0.75
REWIND_SPEED_MAX = 0.25 # delta time between rewinding tiles.

class ExceptionThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None, exception_holder:list|None=None):
        self.exception_holder = exception_holder
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
    def run(self) -> Any:
        self.exception = None
        try:
            self.return_value = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exception = e
            self.exception_holder.append(e)
        finally:
            del self._target, self._args, self._kwargs

class Board(Drawable.Drawable):

    def __init__(self, size:int|tuple[int,int], seed:int=None, colors:int=2, position:tuple[int,int]=(0,0), pixel_size:int=640, restore_objects:list[tuple[Drawable.Drawable,int]]|None=None, children:list[Drawable.Drawable]|None=None, window_size:tuple[int,int]=None) -> None:
        if isinstance(size, int): size = (size, size)
        super().__init__()

        self.hard_mode:bool = Settings.settings["hard_mode"]
        self.has_axis_counters:bool = Settings.settings["axis_counters"]
        self.count_remaining:bool = Settings.settings["count_remaining"]
        self.counters_left = Settings.settings["counters_left"]
        self.counters_top = Settings.settings["counters_top"]

        self.position = position
        self.should_destroy = False
        self.restore_objects = [] if restore_objects is None else restore_objects
        self.children = [] if children is None else children
        largest_size = max(size)
        if self.has_axis_counters: largest_size += 1
        self.pixel_size = pixel_size
        self.display_size = pixel_size / largest_size
        if seed is None: self.seed = LU.get_seed()
        else:self.seed = seed
        self.size = size
        self.colors = colors

        self.__current_mouse_over:int = None
        self.show_locks = False # TODO: make this carry over between board instances.
        self.is_complete = False # True only when the board locks after correctly completing it.
        self.opacity = Animation.Animation(0.0, 0.0, BOARD_FADE_IN_TIME, Bezier.ease_in)
        self.is_finished_loading = False
        self.window_size = window_size
        self.hint_tiles:list[int] = []
        self.is_hinting = False
        self.history:list[tuple[int,int|list[int],int|list[int]]] = []
        # self.history is (index, value_set_to, previous_value)
        self.tile_place_order:list[tuple[int,int]] = [] # list of indexes, corresponding history index; if appended value is already contained then value already contained is removed then appended.
        self.player_board_is_full = False
        self.player_board_fill_time = None
        self.marked_as_complete = False
        self.is_decoupled = False
        self.rewind_state = 0 # 0: not rewinding; 1: rewinding; 2: finished rewinding
        self.rewind_point = None # history index it rewinds to.
        self.since_last_rewind = None # time at which the last tile was changed during rewind.
        self.current_rewind_point = None # history index the rewind is currently at; starts at len(self.history) - 1\
        self.rewind_final_tile:int|None = None # tile to highlight after finish rewind.


        # self.loading_screen_init()
        exception_holder = []
        self.generation_thread = ExceptionThread(target=self.get_board_from_seed, exception_holder=exception_holder)
        self.generation_info = LU.GenerationInfo()
        self.generation_info.exception_holder=exception_holder
        self.generation_thread.start()

    def kill_generator(self) -> None:
        '''Stops the generator from generating and closes the board.'''
        self.should_destroy = True
        self.generation_info.breaker = True

    def delete(self) -> None:
        self.kill_generator()
        super().delete()

    def get_board_from_seed(self) -> list[int]:
        self.full_board, self.empty_board, self.other_data, self.tiles = None, None, None, None
        # return
        self.generation_info.seed = self.seed
        generator_return = LevelCreator.generate(self.size, self.seed, self.colors, self.hard_mode, gen_info=self.generation_info)
        if generator_return is None: return
        self.full_board, self.empty_board, self.other_data = generator_return
        if self.colors == 2:
            self.display_board = self.empty_board[:]
        else:
            DEFAULT = list(range(1, self.colors + 1))
            self.display_board = [(DEFAULT[:] if value == 0 else [value]) for value in self.empty_board]
        self.player_board = self.display_board
        self.init_tiles()
        
        self.children.extend(self.get_additional_children())
        self.start_time = time.time()
        self.is_finished_loading = True
    
    def get_additional_children(self) -> list[Drawable.Drawable]:
        children:list[Drawable.Drawable] = []
        children.append(ButtonPanel.ButtonPanel([("close", (self.button_close,)), ("history", (self.button_undo,)), ("eye", (self.button_hint,))]))
        self.timer_text = Drawable.Drawable(None, (0, 0))
        self.timer_text_content = ""
        children.append(self.timer_text)
        return children

    def get_lock_surface(self) -> pygame.Surface:
        '''Returns a copy of the lock texture, sized and opacitized correctly.'''
        lock_texture = Textures.get("lock")
        lock_size = 0.4 * self.display_size
        lock_surface = pygame.transform.scale(lock_texture, (lock_size, lock_size))
        lock_surface.set_alpha(51) # 0.2 * 255
        return lock_surface

    def init_tiles(self) -> None:
        self.tiles:list[Tile.Tile] = []
        self.axis_counters:list[AxisCounter.AxisCounter] = []
        current_time = time.time()
        lock_surface = self.get_lock_surface()
        width = self.size[0]
        height = self.size[1]
        if self.has_axis_counters: width += 1; height += 1
        for index in range(width * height):
            x = index % width # display position
            y = index // width
            is_row_counter = (self.counters_left and x == 0) or (not self.counters_left and x == width - 1)
            is_column_counter = ((self.counters_top and y == 0) or (not self.counters_top and y == height - 1))

            if self.has_axis_counters and (is_row_counter ^ is_column_counter):
                # axis counters
                axis_x = x; axis_y = y
                if self.counters_left and is_column_counter: axis_x -= 1
                if self.counters_top and is_row_counter: axis_y -= 1
                if is_row_counter:
                    is_top_left = self.counters_left
                    axis_index = axis_y
                    length = self.size[0]
                else:
                    is_top_left = self.counters_top
                    axis_index = axis_x
                    length = self.size[1]
                axis_counter = AxisCounter.AxisCounter([], axis_index, length, self.colors, is_row_counter, self.display_size, current_time, is_top_left, self.count_remaining)
                axis_counter.position = (self.position[0] + x * self.display_size, self.position[1] + y * self.display_size)
                self.axis_counters.append(axis_counter)

            elif self.has_axis_counters and is_row_counter and is_column_counter: pass # the tile in the corner
            else:
                # tiles
                tile_x = x; tile_y = y
                if self.has_axis_counters and self.counters_left: tile_x -= 1
                if self.has_axis_counters and self.counters_top: tile_y -= 1
                tile_index = tile_y * self.size[0] + tile_x # actual index
                is_even = (tile_x + tile_y) % 2 == 1
                if self.tile_is_empty(self.empty_board[tile_index]):
                    start_progress = 0.0
                    can_modify = True
                    is_locked = False
                else:
                    start_progress = 1.0
                    can_modify = False
                    is_locked = True
                tile = Tile.Tile(tile_index, self.display_size, self.display_board[tile_index], is_even, self.colors, current_time, start_progress, is_locked, can_modify, self.show_locks, lock_surface, mode="board")
                tile.position = (self.position[0] + x * self.display_size, self.position[1] + y * self.display_size)
                if tile_index == 0: self.tile_origin = tile.position # where the top left corner of the tiles are. 
                self.tiles.append(tile)

        for axis_counter in self.axis_counters: # pass over axis counters to set the tiles_to_count variable
            if axis_counter.is_row:
                axis_counter.tiles_to_count = self.tiles[axis_counter.index * self.size[0] : (axis_counter.index + 1) * self.size[0]]
                axis_counter.surface = axis_counter.get_surface(current_time)
            else:
                axis_counter.tiles_to_count = self.tiles[axis_counter.index::self.size[0]]
                axis_counter.surface = axis_counter.get_surface(current_time)

        self.children.extend(self.tiles)
        self.children.extend(self.axis_counters)

    def get_timer_text(self) -> None:
        '''Sets the timer text's values.'''
        if self.is_complete:
            elapsed_time = self.final_time
            timer_text = "%s:%s%s" % (str(int(elapsed_time // 60)).zfill(2), str(int(elapsed_time % 60)).zfill(2), ("%.3f" % round(elapsed_time % 1, 3))[1:])
        else:
            elapsed_time = time.time() - self.start_time
            timer_text = "%s:%s" % (str(int(elapsed_time // 60)).zfill(2), str(int(elapsed_time % 60)).zfill(2))
        if timer_text != self.timer_text_content:
            self.timer_text_content = timer_text
            surface = Fonts.board_timer.render(timer_text, True, Colors.get("font"))
            self.timer_text.surface = surface
            bottom_constraint = ButtonPanel.ButtonPanel.top_constraint
            top_constraint = self.position[1] + self.pixel_size
            vertical_space = bottom_constraint - top_constraint
            assert vertical_space > 0
            surface_size = surface.get_size()
            self.timer_text.position = (self.position[0] + (self.pixel_size - surface_size[0]) / 2, bottom_constraint - surface_size[1])

    def display(self) -> pygame.Surface:
        self.get_timer_text()
        current_time = time.time()
        opacity = self.opacity.get(current_time)
        if self.is_finished_loading:
            for index in range(self.size[0] * self.size[1]):
                tile = self.tiles[index]
                tile_surface_requirements = tile.get_conditions(current_time)
                tile.reload_for_board(tile_surface_requirements, current_time)
                self.tiles[index].last_tick_time = current_time
        self.set_alpha(opacity * 255)

    def reload(self, current_time:float) -> None:
        # self.children = []
        # self.init_tiles()
        # self.children.extend(self.get_additional_children())
        return super().reload(current_time)

    def tile_is_empty(self, tile) -> bool:
        if tile == 0: return True
        elif isinstance(tile, list): return len(tile) == self.colors
    
    def decouple(self) -> None:
        '''Separates the display list and truth list.'''
        self.is_decoupled = True
        if isinstance(self.player_board[0], list):
            self.player_board = LU.copy_tiles(self.player_board)
        else: self.player_board = self.player_board[:]
        assert self.display_board is not self.player_board
    
    def recouple_player(self) -> None:
        '''Sets the display board to the player board.'''
        for player_tile_index, player_tile in enumerate(self.player_board):
            self.set_tile(player_tile_index, player_tile)
        self.is_decoupled = False
        self.display_board = self.player_board
        self.rewind_state = 0
    
    def recouple_display(self) -> None:
        '''Sets the player board to the display board.'''
        self.is_decoupled = False
        self.player_board = self.display_board
        self.history = self.history[:self.rewind_point]
        self.tile_place_order = self.tile_place_order[:self.rewind_place_point]
        self.rewind_state = 0

    def rewind(self, history_point:int, place_point:int) -> None:
        '''Will *visually* rewind the board to the specified index in history.'''
        self.can_modify = False
        self.decouple()
        self.rewind_state = 1
        self.rewind_point = history_point # where it's rewinding to
        self.rewind_place_point = place_point
        self.since_last_rewind = 0 # use 0 instead of current time so it instantly rewinds the first tile
        self.current_rewind_point = len(self.history) - 1
        self.rewind_speed = min(REWIND_SPEED_MAX, 1.0/(1 + self.current_rewind_point - self.rewind_point))
        self.rewind_final_tile = self.history[history_point][0]

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
            self.is_complete = True
            self.final_time = self.player_board_fill_time - self.start_time
            self.opacity.set(0.0, BOARD_FADE_OUT_TIME_COMPLETE)
            for child in self.children:
                if isinstance(child, Button.Button):
                    child.enabled = False
                elif isinstance(child, ButtonPanel.ButtonPanel):
                    child.disable()
            for tile in self.tiles:
                tile.can_modify = False
        else:
            first_error_tile, first_error_history_index, first_error_place_index = self.get_first_error_tile()
            self.rewind(first_error_history_index, first_error_place_index)

    def button_close(self) -> None:
        self.recouple_player()
        self.opacity.set(0.0, BOARD_FADE_OUT_TIME_CLOSE)
        for child in self.children:
            if isinstance(child, Button.Button):
                child.enabled = False
            elif isinstance(child, ButtonPanel.ButtonPanel):
                child.disable()
        for tile in self.tiles:
            tile.can_modify = False

    def button_undo(self) -> None:
        match self.rewind_state:
            case 0: pass
            case 1: # during rewind; it makes it rewind one unit further.
                if self.rewind_point >= 0:
                    self.rewind_point -= 1
                target_tile_index = self.history[self.rewind_point][0]
                for place_index, place in enumerate(self.tile_place_order):
                    if place[0] == target_tile_index:
                        self.rewind_place_point = place_index
                        break
                self.rewind_final_tile = self.history[self.rewind_point][0]
                return
            case 2: # end of rewind; undoing undoes from the display position.
                self.recouple_display()
                self.unhighlight()
                pass
        if len(self.history) == 0: return
        self.unhighlight()
        index, post, pre = self.history.pop()
        for tile_place_index, tile_place in enumerate(self.tile_place_order):
            if tile_place[1] == index: del self.tile_place_order[tile_place_index]
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

    def get_first_error_tile(self) -> tuple[int,int,int]|None:
        '''Returns the first tile index in `self.tile_place_order` that does not match the full board, the history index, and the tile_place_order index.'''
        for index, tile_place_order in enumerate(self.tile_place_order):
            tile_index, history_index = tile_place_order
            player_value = self.player_board[tile_index]
            true_value = self.full_board[tile_index]
            if isinstance(player_value, list):
                if player_value[0] != true_value: return tile_index, history_index, index
            else:
                if player_value != true_value: return tile_index, history_index, index
        else: return None

    def button_hint(self) -> None:
        match self.rewind_state:
            case 0: pass
            case 1 | 2: # end of rewind
                self.unhighlight()
                self.recouple_player()
                return
        if self.is_hinting:
            self.unhighlight()
        else:
            self.unhighlight()
            hint = LevelHinter.get_hint(self.size, self.colors, self.player_board, self.full_board)
            if hint.is_incorrect_hint:
                first_error_tile, first_error_history_index, first_error_place_index = self.get_first_error_tile()
                self.rewind(first_error_history_index, first_error_place_index)
            else:
                tile_indexes = hint.tiles_affected
                if isinstance(hint.target_tile, int): tile_indexes.append(hint.target_tile)
                self.highlight(tile_indexes)

    def tile_violates_solution(self, index:int, value:int|list[int]|None=None) -> bool:
        if value is None: value = self.player_board[index]
        if isinstance(value, list):
            return self.full_board[index] not in value
        else: return value != self.full_board[index] and value != 0

    def new_history(self, tile_index:int, next_value:int|list[int], previous_value:int|list[int]) -> None:
        self.history.append((tile_index, next_value, previous_value))
        for index, tile_place_index in enumerate(self.tile_place_order):
            if tile_index == tile_place_index[0]:
                del self.tile_place_order[index]
                break
        default = list(range(1, self.colors + 1)) if self.colors != 2 else 0
        if next_value != default: self.tile_place_order.append((tile_index, len(self.history) - 1))

    def set_tile(self, index:int, value:int|list[int]) -> None:
        self.tiles[index].click_time = time.time()
        if isinstance(value, list):
            for color in range(1, self.colors + 1):
                self.tiles[index].set_value_multi(color, color in value)
        else:
            self.tiles[index].set_value(value)

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[int,int]) -> list[tuple[Drawable.Drawable]]|None:
        def get_relative_mouse_position(position:tuple[float,float]|None=None) -> tuple[float,float]:
            if position is None: position = event.__dict__["pos"]
            return position[0] - self.tile_origin[0], position[1] - self.tile_origin[1]
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
            if not self.tiles[index].can_modify: # if it is a locked tile
                self.tiles[index].click_time_locked = time.time()
                if self.tiles[index].is_locked:
                    self.show_locks = not self.show_locks
                    self.update_locks()
                return
            else:
                self.tiles[index].click_time = time.time()
            if self.rewind_state == 2: self.recouple_display()
            if self.colors == 2:
                current_value = self.player_board[index]
                next_value = current_value + up_values[event.__dict__["button"]]
                next_value = next_value % (self.colors + 1)
                self.player_board[index] = next_value
                self.tiles[index].set_value(next_value)
                self.new_history(index, next_value, current_value)
                self.unhighlight()
                self.player_board_is_full = 0 not in self.player_board
            else:
                previous_value = self.player_board[index][:]
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
                self.new_history(index, self.player_board[index][:], previous_value)
            if self.player_board_is_full: self.player_board_fill_time = time.time()
            self.marked_as_complete = False

        def mouse_motion() -> None:
            index = get_index()
            if index is None:
                if self.__current_mouse_over is not None:
                    self.tiles[self.__current_mouse_over].stop_mousing_over(current_time)
                    self.__current_mouse_over = None
                return
            if index != self.__current_mouse_over:
                if self.__current_mouse_over is not None:
                    self.tiles[self.__current_mouse_over].stop_mousing_over(current_time)
                if index >= len(self.tiles): raise IndexError("list index (%i) out of range of %s" % (index, str(self.tiles)))
                self.tiles[index].start_mousing_over(current_time)
            self.__current_mouse_over = index
        def mouse_leave() -> None:
            if self.__current_mouse_over is not None:
                self.tiles[self.__current_mouse_over].is_mousing_over = False
            self.__current_mouse_over = None
        
        def key_down() -> None:
            key = event.__dict__["key"]
        
        def key_up() -> None:
            key = event.__dict__["key"]
        
        current_time = time.time()

        for event in events:
            match event.type:
                case pygame.MOUSEBUTTONDOWN: mouse_button_down()
                case pygame.MOUSEMOTION: mouse_motion()
                case pygame.WINDOWLEAVE: mouse_leave()
                case pygame.KEYDOWN: key_down()
                case pygame.KEYUP: key_up()
        
        if self.is_finished_loading and self.opacity.is_finished() and self.opacity.get(current_time) == 0.0:
            self.should_destroy = True
            for child in self.children:
                child.should_destroy = True
        if self.player_board_is_full and not self.marked_as_complete and current_time - self.player_board_fill_time >= COMPLETION_WAIT_TIME:
            self.mark_as_complete()
        if self.rewind_state == 1:
            # while rewinding
            if current_time - self.since_last_rewind >= self.rewind_speed:
                self.since_last_rewind = current_time
                tile_index, next_value, previous_value = self.history[self.current_rewind_point]

                self.set_tile(tile_index, previous_value)
                if self.colors == 2: self.display_board[tile_index] = previous_value
                self.current_rewind_point -= 1
        if self.rewind_state == 1 and self.current_rewind_point == self.rewind_point - 1:
            # finish rewinding
            self.rewind_state = 2
            self.can_modify = True
            if self.rewind_final_tile is not None: self.highlight([self.rewind_final_tile])
