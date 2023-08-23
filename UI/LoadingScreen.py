from collections.abc import Callable
import time

import pygame

import UI.ButtonPanel as ButtonPanel
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

LOADING_BAR_WIDTH = 0.75 # ratio of display width
LOADING_BAR_HEIGHT = 20
LOADING_BAR_RADIUS = 10 # radius
LOADING_BAR_BORDER_WIDTH = 1

class LoadingBar(Drawable.Drawable):
    def __init__(self, width:int, parent:"LoadingScreen", color_name:str, position:tuple[int,int], restore_objects:list[tuple[Drawable.Drawable,int]]|None=None, children:list[Drawable.Drawable]|None=None) -> None:
        self.width = width
        self.parent = parent
        self.color_name = color_name # color to fill the complete portion with.
        self.progress = 0.0
        super().__init__(self.get_surface(), position, restore_objects, children)
    
    def get_progress(self) -> float:
        gen_progress = self.parent.board.generation_info.generation_progress
        return self.progress + (gen_progress - self.progress) * 0.5

    def get_surface(self) -> pygame.Surface:
        behind = pygame.Surface((self.width, LOADING_BAR_HEIGHT), pygame.SRCALPHA)
        mask = pygame.Surface((self.width, LOADING_BAR_HEIGHT), pygame.SRCALPHA)
        surface = pygame.Surface((self.width, LOADING_BAR_HEIGHT), pygame.SRCALPHA)
        self.progress = self.get_progress()
        assert self.progress >= 0.0; assert self.progress <= 1.0
        self.last_progress = self.progress

        incomplete_color = Colors.get("loading_bar.incomplete")
        filled_color = Colors.get(self.color_name)
        border_color = Colors.get("loading_bar.border")
        mask_color1 = Colors.get_non_conflicting_colors([incomplete_color, filled_color, border_color])
        mask_color2 = Colors.get_non_conflicting_colors([incomplete_color, filled_color,border_color, mask_color1])

        behind.fill(incomplete_color)
        behind.fill(filled_color, pygame.Rect(0, 0, self.width * self.progress, LOADING_BAR_HEIGHT))
        r = LOADING_BAR_RADIUS
        mask.fill(mask_color1)
        pygame.draw.rect(mask, mask_color2, pygame.Rect(0, LOADING_BAR_HEIGHT / 2 - r, self.width, r * 2), border_radius=r)
        surface.blit(behind, (0, 0))
        mask.set_colorkey(mask_color2)
        surface.blit(mask, (0, 0))
        surface.set_colorkey(mask_color1)
        pygame.draw.rect(surface, border_color, pygame.Rect(0, LOADING_BAR_HEIGHT / 2 - r, self.width, r * 2), border_radius=r, width=LOADING_BAR_BORDER_WIDTH)
        return surface
    
    def display(self) -> pygame.Surface:
        self.surface = self.get_surface()
        return super().display()

    def reload(self, current_time:float) -> None:
        self.surface = self.get_surface()
        return super().reload(current_time)

class LoadingScreen(Drawable.Drawable):
    def __init__(self, board:Board.Board, board_size:tuple[float,float], display_size:tuple[float,float], exit_function:Callable[[],list[tuple[Drawable.Drawable,int]]], surface:pygame.Surface|None=None, position:tuple[int,int]|None=None, restore_objects:list[tuple[Drawable.Drawable,int]]|None=None, children:list[Drawable.Drawable]|None=None) -> None:

        self.board = board
        self.board_size = board_size
        self.display_size = display_size
        self.exit_function = exit_function
        self.position = position

        self.is_fading = False
        self.previous_progress = None
        self.closed_early = False
        self.loading_start_time = time.time()
        self.opacity = Animation.Animation(1.0, 0.0, LOADING_FADE_IN_TIME, Bezier.ease_in)

        self.calculate_sizes()
        if children is None: children = []
        # super().__init__(surface, position, restore_objects, children + [self.loading_tile, self.loading_text, self.button_panel, self.progress_text])
        super().__init__(surface, position, restore_objects, children + [self.loading_bar, self.progress_text, self.loading_text, self.button_panel])

    def button_close(self) -> None:
        self.opacity.set(0.0, LOADING_FADE_OUT_TIME)
        self.is_fading = True
        self.closed_early = True
        self.board.kill_generator()
        self.restore_objects.extend(self.board.restore_objects)

    def calculate_sizes(self) -> None:
        # loading_tile_size = LOADING_TILE_SIZE * min(self.board_size)
        # self.loading_tile = Tile.Tile(0, loading_tile_size, self.board.colors, False, 2, self.opacity.get(), mode="loading")
        # self.loading_tile.position = (self.position[0] + (self.board_size[0] - loading_tile_size) / 2, self.position[1] + (self.board_size[1] - loading_tile_size) / 2)

        loading_text = Fonts.loading_screen.render("Loading", True, Colors.get("font"))
        loading_text_size = loading_text.get_size()
        loading_text_position = (self.position[0] + (self.board_size[0] - loading_text_size[0]) / 2, self.position[1] + (self.board_size[1] * 0.25 - loading_text_size[1]) / 2)
        self.loading_text = Drawable.Drawable(loading_text, loading_text_position)

        self.loading_bar = LoadingBar(self.board_size[0] * LOADING_BAR_WIDTH, self, Tile.get_color_name(self.board.colors, False), (0, 0))
        loading_bar_size = self.loading_bar.surface.get_size()
        self.loading_bar.position = (self.position[0] + (self.board_size[0] - loading_bar_size[0]) / 2, self.position[1] + (self.board_size[1] * 1.0 - loading_bar_size[1]) / 2)

        progress_text = Fonts.loading_screen_progress.render("0%", True, Colors.get("font.loading_screen_progress"))
        progress_text_size = progress_text.get_size()
        progress_text_position = (self.position[0] + (self.board_size[0] - progress_text_size[0]) / 2, self.position[1] + (self.board_size[1] * 1.0 - progress_text_size[1]) / 2 - loading_bar_size[1] * 1.5)
        self.progress_text = Drawable.Drawable(progress_text, progress_text_position)

        self.button_panel = ButtonPanel.ButtonPanel([("close", (self.button_close,))])

    def display(self) -> pygame.Surface|None:
        # self.loading_tile.surface = self.loading_tile.reload_for_loading(self.loading_start_time - time.time())
        # loading_tile_size = self.loading_tile.surface.get_size()
        # self.loading_tile.position = (self.position[0] + (self.board_size[0] - loading_tile_size[0]) / 2, self.position[1] + (self.board_size[1] - loading_tile_size[1]) / 2)

        if self.previous_progress != self.board.generation_info.generation_progress:
            self.progress_text.surface = Fonts.loading_screen_progress.render(str(int(100 * self.board.generation_info.generation_progress)) + "%", True, Colors.get("font.loading_screen_progress"))
            progress_text_size = self.progress_text.surface.get_size()
            self.progress_text.position = (self.position[0] + (self.board_size[0] - progress_text_size[0]) / 2, self.progress_text.position[1])
            self.previous_progress = self.board.generation_info.generation_progress

        self.set_alpha(255 * self.opacity.get())
    
    def reload(self, current_time:float) -> None:
        self.calculate_sizes()
        return super().reload(current_time)

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[int,int]) -> list[tuple[Drawable.Drawable]]|None:
        if self.board.is_finished_loading and not self.is_fading:
            self.opacity.set(0.0, LOADING_FADE_OUT_TIME)
            self.is_fading = True
        if (self.board.is_finished_loading or self.closed_early) and self.opacity.get() == 0.0:
            self.should_destroy = True
            return self.exit_function(self)