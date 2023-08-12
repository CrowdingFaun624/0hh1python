import time
from collections.abc import Callable

import pygame

import UI.Board as Board
import UI.Button as Button
import UI.ButtonPanel as ButtonPanel
import UI.Colors as Colors
import UI.Drawable as Drawable
import UI.Fonts as Fonts
import UI.SettingsMenu as SettingsMenu
import UI.Tile as Tile
import Utilities.Animation as Animation
import Utilities.Bezier as Bezier

LEVELS = {2: [4, 6, 8, 10, 12, 14, 16, 18, 20], 3: [6, 9, 12, 15]}
SECTION_PADDING_SIZE = 0.125
MAX_PER_ROW = 3
FADE_TIME = 0.1
MAXIMUM_BOARD_SIZE = 640

class LevelSelector(Drawable.Drawable):
    def __init__(self, display_size:tuple[int,int], exit_function:Callable[["LevelSelector"],list[tuple[Drawable.Drawable,int]]], settings_function:Callable[["LevelSelector"],list[tuple[Drawable.Drawable,int]]], position:tuple[int,int]=None, restore_objects:list[tuple[Drawable.Drawable,int]]|None=None, children:list[Drawable.Drawable]|None=None) -> None:
        self.display_size = display_size
        self.exit_function = exit_function
        self.settings_function = settings_function
        self.board_settings = None
        self.is_fading_out = False
        self.has_returned_level = False
        self.enabled = True
        self.opacity = Animation.Animation(1.0, 0.0, FADE_TIME, Bezier.ease_in)
        self.surface = self.get_surface()
        if children is None: children = []
        button_panel = ButtonPanel.ButtonPanel([("cog.png", (self.settings_function,[self]))], self.position[1] + self.surface.get_size()[1], self.display_size[1], self.position[0], self.position[0] + self.surface.get_size()[0])
        super().__init__(self.surface, self.position, restore_objects, children + [button_panel])

    def calculate_sizes(self) -> None:
        '''Calculates variables used for sizing stuff. Call this function if the window size changes.'''
        rows:list[list[tuple[int,int]]|None] = [] # list-type items are rows of (color, size); None are separators
        for color, levels in LEVELS.items():
            row:list[tuple[int,int]] = []
            for level in levels:
                row.append((color, level))
                if len(row) == MAX_PER_ROW:
                    rows.append(row)
                    row = []
            if len(row) > 0: rows.append(row)
            rows.append(None)
        rows.pop() # remove trailing None

        self.total_colors = len(LEVELS)
        self.max_row_length = max((len(levels) for levels in rows if levels is not None))
        self.tile_size = min(128, int(self.display_size[0] * 0.75 / self.max_row_length), int(self.display_size[1] * 0.75 / (len(rows) - rows.count(None) + SECTION_PADDING_SIZE * rows.count(None))))
        self.section_padding_size = int(self.tile_size * SECTION_PADDING_SIZE)
        self.max_width = self.tile_size * self.max_row_length
        self.total_height = self.tile_size * (len(rows) - rows.count(None)) + (rows.count(None)) * self.section_padding_size
        self.position = (self.display_size[0] / 2 - self.max_width / 2, self.display_size[1] / 2 - self.total_height / 2)

        color_patterns:dict[int,list[int]] = dict((color, [((color - i) % color) + 1 for i in range(len(LEVELS[color]), 0, -1)] if len(LEVELS[color]) > color else list(range(color, 0, -1))[:len(LEVELS[color])]) for color in LEVELS)
        self.tiles_positions:list[tuple[tuple[int,int,int,int,int],tuple[int,int]]] = [] # [(color, size), (x_position, y_position), ...]
        x_position, y_position = 0, 0 # pixels
        x, y = 0, 0 # tiles
        index = 0
        for row in rows:
            if row is None: y_position += self.section_padding_size; y = 0; index = 0; continue
            x_position = 0
            x = 0
            for tile in row:
                color, level = tile
                display_color = color_patterns[color][index]
                tile_data = (color, level, display_color, x, y)
                self.tiles_positions.append((tile_data, (x_position, y_position)))
                x += 1
                x_position += self.tile_size
                index += 1
            y_position += self.tile_size
            y += 1

    def get_surface(self) -> pygame.Surface:
        self.calculate_sizes()
        font = Fonts.get_font("josefin", int(self.tile_size / 2))
        surface = pygame.Surface((self.max_width, self.total_height), pygame.SRCALPHA)
        current_time = time.time()
        for tile, position in self.tiles_positions:
            color, level, display_color, x, y = tile; x_position, y_position = position
            is_even = is_even = (x + y) % 2 == 1
            tile_object = Tile.Tile(0, self.tile_size, display_color, is_even, 2, current_time)
            surface.blit(tile_object.surface, (x_position, y_position))
            font_surface = font.render(str(level), True, Colors.font)
            font_size = font_surface.get_size()
            font_x, font_y = (self.tile_size / 2 - font_size[0] / 2, self.tile_size / 2 - font_size[1] / 2)
            surface.blit(font_surface, (x_position + font_x, y_position + font_y)) # TODO: font vertical positioning is messed up.
        return surface

    def display(self) -> pygame.Surface:
        self.set_alpha(255 * self.opacity.get())
        return self.surface

    def restore(self) -> None:
        self.should_destroy = False
        self.board_settings = None
        self.is_fading_out = False
        self.enabled = True
        for child in self.children:
            if isinstance(child, Button.Button): child.enabled = True
        self.has_returned_level = False
        self.opacity.set(1.0)

    def settings_button(self) -> list[tuple[Drawable.Drawable,int]]:
        self.opacity.set(0.0)
        self.enabled = False
        self.is_fading_out = True
        for child in self.children:
            if isinstance(child, Button.Button): child.enabled = False
        return [(SettingsMenu.SettingsMenu(self.display_size, restore_objects=[(self, -1)]), 1)]

    def tick(self, events:list[pygame.event.Event], screen_position:list[int,int]) -> list[tuple[Drawable.Drawable,int]]|None:
        def get_relative_mouse_position(position:tuple[float,float]|None=None) -> tuple[float,float]:
            if position is None: position = event.__dict__["pos"]
            return position[0] - screen_position[0], position[1] - screen_position[1]
        def mouse_button_down() -> None:
            mouse_position = get_relative_mouse_position()
            if not self.enabled: return
            for tile, position, in self.tiles_positions:
                color, level, _, _, _ = tile
                x_position, y_position = position
                if mouse_position[0] > x_position and mouse_position[0] <= x_position + self.tile_size and mouse_position[1] > y_position and mouse_position[1] <= y_position + self.tile_size:
                    self.opacity.set(0.0)
                    self.board_settings = (level, color)
                    self.is_fading_out = True
                    self.enabled = False
                    for child in self.children:
                        if isinstance(child, Button.Button): child.enabled = False

        for event in events:
            match event.type:
                case pygame.MOUSEBUTTONDOWN: mouse_button_down()
        
        current_time = time.time()
        if self.is_fading_out and self.opacity.get(current_time) == 0.0: self.should_destroy = True

        if self.is_fading_out and not self.has_returned_level and self.board_settings is not None:
            self.has_returned_level = True


            return self.exit_function(self)
