from collections.abc import Callable
import time

import pygame

import UI.Colors as Colors
import UI.Drawable as Drawable
import UI.Fonts as Fonts
import UI.Board as Board
import UI.Tile as Tile
import Utilities.Animation as Animation
import Utilities.Bezier as Bezier

LOADING_FADE_IN_TIME = 0.3
LOADING_FADE_OUT_TIME = 0.1
LOADING_TILE_SIZE = 0.5

class LoadingScreen(Drawable.Drawable):
    def __init__(self, board:Board.Board, board_size:tuple[float,float], exit_function:Callable[[],list[tuple[Drawable.Drawable,int]]], surface:pygame.Surface|None=None, position:tuple[int,int]|None=None, restore_objects:list[tuple[Drawable.Drawable,int]]|None=None, children:list[Drawable.Drawable]|None=None) -> None:

        self.board = board
        self.board_size = board_size
        self.exit_function = exit_function

        self.position = position
        self.is_fading = False


        self.loading_start_time = time.time()
        self.opacity = Animation.Animation(1.0, 0.0, LOADING_FADE_IN_TIME, Bezier.ease_in)

        self.calculate_sizes()
        if children is None: children = []
        super().__init__(surface, position, restore_objects, children + [self.loading_tile, self.loading_text])

    def calculate_sizes(self) -> None:
        loading_tile_size = LOADING_TILE_SIZE * min(self.board_size)
        self.loading_tile = Tile.Tile(0, loading_tile_size, self.board.colors, False, 2, self.opacity.get(), mode="loading")
        self.loading_tile.previous_value = None
        loading_text = Fonts.loading_screen.render("Loading", True, Colors.get("font"))
        loading_text_size = loading_text.get_size()
        loading_text_position = (self.position[0] + (self.board_size[0] - loading_text_size[0]) / 2, self.position[1] + (self.board_size[1] * 0.25 - loading_text_size[1]) / 2)
        self.loading_text = Drawable.Drawable(loading_text, loading_text_position)

    def display(self) -> pygame.Surface|None:
        self.loading_tile.surface = self.loading_tile.reload_for_loading(self.loading_start_time - time.time())
        loading_tile_size = self.loading_tile.surface.get_size()
        self.loading_tile.position = (self.position[0] + (self.board_size[0] - loading_tile_size[0]) / 2, self.position[1] + (self.board_size[1] - loading_tile_size[1]) / 2)
        self.set_alpha(255 * self.opacity.get())
    
    def reload(self, current_time:float) -> None:
        self.calculate_sizes()
        return super().reload(current_time)

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[int,int]) -> list[tuple[Drawable.Drawable]]|None:
        if self.board.is_finished_loading and not self.is_fading:
            self.opacity.set(0.0, LOADING_FADE_OUT_TIME)
            self.is_fading = True
        if self.board.is_finished_loading and self.opacity.get() == 0.0:
            self.should_destroy = True
            return self.exit_function(self)