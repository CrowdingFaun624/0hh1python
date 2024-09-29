import math
import time
from typing import Any, cast

import pygame

import UI.Colors as Colors
import UI.Drawable as Drawable
import UI.Fonts as Fonts
import UI.Textures as Textures
import UI.Tile as Tile
import Utilities.Animation as Animation
import Utilities.Bezier as Bezier

COUNTERS_OPACITY_TIME = 0.25
CHECK_OPACITY_TIME = 0.1

def secant(theta:float) -> float:
    cos = math.cos(theta)
    if cos == 0: return float("Infinity")
    else: return 1 / cos
def cosecant(theta:float) -> float:
    sin = math.sin(theta)
    if sin == 0: return float("Infinity")
    else: return 1 / sin

class AxisCounter(Tile.Tile):
    def __init__(self, tiles_to_count:list[Tile.Tile], axis_index:int, length:int, colors:int, is_row:bool, display_size:float, current_time:float, is_top_left:bool=True, show_remainder:bool=True, counters:bool=True, checkboxes:bool=False) -> None:
        self.tiles_to_count = tiles_to_count
        self.is_row = is_row
        self.length = length
        self.is_top_left = is_top_left
        self.show_remainder = show_remainder
        self.counters = counters
        self.checkboxes = checkboxes


        self.previous_state:list[Any]|None = None
        self.previous_tiles_values:list[int|list[int]]|None = None
        self.checked = False
        self.enabled = True
        self.opacity = 0.0
        self.opacity_animations = [Animation.Animation(1.0, None, COUNTERS_OPACITY_TIME, Bezier.ease_out, current_time) for i in range(colors)]
        self.check_opacity = Animation.Animation(float(self.checked), float(self.checked), CHECK_OPACITY_TIME, Bezier.ease_out, current_time)
        if self.checkboxes:
            if self.counters: shrink_coefficient = 5
            else: shrink_coefficient = 2
            self.check_texture = Textures.get("check")
            self.check_texture = pygame.transform.scale(self.check_texture, (int(display_size / shrink_coefficient), int(display_size / shrink_coefficient)))

        if not (counters or checkboxes): raise ValueError("AxisCounter summoned as neither a counter nor checkbox!")
        super().__init__(axis_index, display_size, list(range(1, colors + 1)), axis_index % 2 == 0, colors, current_time, empty_color_name="background", multicolor_transparencies=(0.0, 0.25, 0.25))

    def get_surface(self, current_time:float) -> pygame.Surface:
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        if self.counters:
            counter_surface = self.get_counter_surface(current_time)
            if counter_surface is not None:
                surface.blit(counter_surface, (0, 0))
        if self.checkboxes:
            surface.blit(self.get_checkbox_surface(current_time), (0, 0))
        return surface

    def get_checkbox_surface(self, current_time:float) -> pygame.Surface:
        base_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        check_opacity = self.check_opacity.get(current_time)
        if check_opacity != 0.0:
            check_size = self.check_texture.get_size()
            check_position = ((self.size - check_size[0]) / 2, (self.size - check_size[1]) / 2)
            base_surface.blit(self.check_texture, check_position)
            base_surface.set_alpha(int(255 * check_opacity))
        return base_surface

    def get_counter_surface(self, current_time:float) -> pygame.Surface|None:
        if len(self.tiles_to_count) != self.length: return None
        full_counts, all_counts = self.get_count()
        size = int(self.length // self.colors)
        full_remainders = [size - count for count in full_counts]
        all_remainders = [count - size for count in all_counts]
        self.previous_count = (full_counts, all_counts)

        counts = full_counts
        remainders = full_remainders
        other_remainders = all_remainders

        font_colors:list[pygame.Color] = []
        text_opacities:list[float] = [] # controls opacity of tile sections as well as text opacity.
        for remainder, other_remainder in zip(remainders, other_remainders):
            match max(min(remainder, 1), -1):
                case -1:
                    font_colors.append(Colors.get("font.axis_counter.bad"))
                    text_opacities.append(1.0)
                case 0:
                    if other_remainder == 0:
                        font_colors.append(Colors.get("font.axis_counter.normal")) # This means that the player has already done what they can, and no more placing can satisfy this.
                        text_opacities.append(0.0)
                    else:
                        font_colors.append(Colors.get("font.axis_counter.complete"))
                        text_opacities.append(1.0)
                case 1:
                    font_colors.append(Colors.get("font.axis_counter.normal"))
                    text_opacities.append(1.0)
        (opacity_animation.set(value) for value, opacity_animation in zip(text_opacities, self.opacity_animations) if value != opacity_animation.next_value)
        if any(self.set_value_multi(color_index + 1, bool(value)) for color_index, value in enumerate(text_opacities)):
            self.click_time = current_time
        if self.show_remainder: counts = remainders
        texts = [str(count) for count in counts]
        base_surface = self.get_surface_multicolor(current_time)
        ray_directions = [(math.tau / self.colors) * i for i in range(self.colors)]
        ray_lengths = [(self.size / 2) * min(abs(secant(theta)), abs(cosecant(theta))) for theta in ray_directions]
        text_centers = [((self.size / 2 + (ray_length / 2) * math.sin(ray_direction)), self.size / 2 + (ray_length / 2) * -math.cos(ray_direction)) for ray_length, ray_direction in zip(ray_lengths, ray_directions)]
        font = Fonts.get_font("josefin", (math.pi / self.colors) * self.size * 0.25)
        font_surfaces = [font.render(text, True, font_color) for text, font_color in zip(texts, font_colors)]
        for text_opacity, font_surface in zip(text_opacities, font_surfaces): font_surface.set_alpha(int(text_opacity * 255))
        base_surface.blits([(font_surface, (text_center[0] - font_surface.get_width() / 2, text_center[1] - font_surface.get_height() / 2)) for font_surface, text_center in zip(font_surfaces, text_centers)])
        return base_surface

    def get_count(self) -> tuple[list[int],list[int]]:
        '''Returns the full count and the all count.'''
        values = [tile.value for tile in self.tiles_to_count]
        if len(self.tiles_to_count) != self.length: return [], []
        if isinstance(self.tiles_to_count[0].value, list):
            full_count = [0] * self.colors
            all_count = [0] * self.colors
            for value in cast(list[list[int]], values):
                if len(value) == 1:
                    full_count[value[0] - 1] += 1
                    all_count[value[0] - 1] += 1
                else:
                    for color in value:
                        all_count[color - 1] += 1
        else:
            full_count = [values.count(color) for color in range(1, self.colors + 1)]
            empty_count = values.count(0)
            all_count = [full + empty_count for full in full_count]
        return full_count, all_count

    def display(self) -> pygame.Surface|None:
        current_time = time.time()
        current_state, current_tiles_values = self.get_conditions(current_time)
        if current_state != self.previous_state:
            self.previous_state = current_state
            self.surface = self.get_surface(current_time)
        if current_tiles_values != self.previous_tiles_values:
            self.previous_tiles_values = current_tiles_values
            self.checked = False
        if self.surface is not None: self.surface.set_alpha(int(255 * self.opacity))
        return super().display()

    def get_conditions(self, current_time:float) -> tuple[list[Any],list[int|list[int]]]:
        conditions:list[Any] = []
        time_since_click = current_time - self.click_time
        if len(self.tiles_to_count) == 0: pass
        if isinstance(self.tiles_to_count[0].value, int):
            tiles_values = [tile.value for tile in self.tiles_to_count]
        else: tiles_values = [tile.value[:] for tile in self.tiles_to_count]
        conditions.append(tiles_values)
        conditions.append(self.checked)
        conditions.append(self.check_opacity.get(current_time))
        if time_since_click <= Tile.TRANSITION_TIME: conditions.append(time_since_click)
        return conditions, tiles_values

    def set_alpha(self, value:int, this_surface:pygame.Surface|None=None) -> None:
        self.opacity = value / 255
        return super().set_alpha(value, this_surface)

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[float, float]) -> list[Drawable.Drawable]|None:

        def mouse_button_down() -> None:
            if not self.enabled: return
            mouse_x, mouse_y = event.__dict__["pos"]
            if mouse_x > screen_position[0] and mouse_y > screen_position[1] and mouse_x <= screen_position[0] + self.size and mouse_y <= screen_position[1] + self.size:
                self.checked = not self.checked
                self.check_opacity.set(float(self.checked))

        for event in events:
            match event.type:
                case pygame.MOUSEBUTTONDOWN: mouse_button_down()
