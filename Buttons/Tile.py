import math
import pygame

import Drawable
import Colors
import Utilities.Animations as Animations
import Utilities.Bezier as Bezier

LOCK_SHAKE_TIME = 0.5 # when locked tile is interacted with
TRANSITION_TIME = 0.2 # from one color to another
REVEAL_TIME = 0.2 # reveal contents in multicolor mode

class Tile(Drawable.Drawable):
    def __init__(self, size:int=160, value:int=0, is_even:bool=False) -> None:
        self.size = size
        self.value = value
        self.is_even = is_even
        super().__init__(None)

    def new_surface(self, ticks:int, current_time:float, tile_data:dict[str,any], board_data:dict[str,any]) -> pygame.Surface:
        self.__tile_data = tile_data
        if board_data["colors"] == 2:
            return self.__get_surface_normal(ticks, current_time, tile_data, board_data)
        else:
            return self.__get_surface_multicolor(ticks, current_time, tile_data, board_data)

    def __position(self, x:float, y:float) -> tuple[float, float]:
        if self.rotation == 0: return x, y
        offset = self.size / 2
        new_x = (x - offset) * self.cos_rotation - (y - offset) * self.sin_rotation + offset
        new_y = (x - offset) * self.sin_rotation + (y - offset) * self.cos_rotation + offset
        return new_x, new_y
    def __get_circle_quarters(self, top_right:bool, top_left:bool, bottom_left:bool, bottom_right:bool) -> tuple[bool,bool,bool,bool]:
        if self.rotation != 0: return True, True, True, True
        else: return top_right, top_left, bottom_left, bottom_right

    def __get_surface_normal(self, ticks:int, current_time:float, tile_data:dict[str,any], board_data:dict[str,any]) -> pygame.Surface:
        if self.__tile_data["click_type"] == "locked": color_ratio = 1.0
        else:
            if self.__tile_data["previous_tile"] is None or current_time - self.__tile_data["click_time"] > TRANSITION_TIME:
                color_ratio = 1.0
            else: color_ratio = self.__get_color_ratio(current_time, TRANSITION_TIME, self.__tile_data["click_time"])
        current_color = self.__get_tile_color()
        previous_color = self.__get_tile_color(self.__tile_data["previous_tile"])
        color = self.__blend_colors(current_color, previous_color, color_ratio)
        self.__get_rotation(current_time, LOCK_SHAKE_TIME)
        padding_size = 0.04 * self.size
        tile_size = self.size - (padding_size * 2)
        border_radius = self.size * 0.1
        shadow_radius = tile_size * 0.06
        
        button_surface = self.__draw_body(padding_size, border_radius, color)
        if self.value != 0:
            button_surface.blit(self.__draw_shadow(padding_size, shadow_radius), (0, 0))
        return button_surface

    def __get_surface_multicolor(self, ticks:int, current_time:float, tile_data:dict[str,any], board_data:dict[str,any]) -> pygame.Surface:
        def get_multicolor(value:list[int], previous_value:list[int]) -> pygame.Surface:
            mask = self.__draw_body(padding_size, border_radius, pygame.Color(0, 0, 0))
            return self.__draw_multicolor(padding_size, value, previous_value, board_data["colors"], current_time, mask)
        def get_full_color(value:int, previous_value:int) -> pygame.Surface:
            if self.__tile_data["click_type"] == "locked": color_ratio = 1.0
            else:
                if previous_value is None or current_time - self.__tile_data["click_time"] > TRANSITION_TIME:
                    color_ratio = 1.0
                else: color_ratio = self.__get_color_ratio(current_time, TRANSITION_TIME, self.__tile_data["click_time"])
            current_color = self.__get_tile_color(value)
            previous_color = self.__get_tile_color(previous_value)
            color = self.__blend_colors(current_color, previous_color, color_ratio)
            return self.__draw_body(padding_size, border_radius, color)
        def is_type_transition() -> bool:
            return (len(self.value) == 1 and len(self.__tile_data["previous_tile"]) == 2) or (len(self.value) == 2 and len(self.__tile_data["previous_tile"]) == 1)
        def single_color_to_int(tile:list[int]) -> int:
            '''Returns the first item of the list, or 0 if it does not exist'''
            if len(tile) == 1: return tile[0]
            else: return 0
        padding_size = 0.04 * self.size
        tile_size = self.size - (padding_size * 2)
        border_radius = self.size * 0.1
        shadow_radius = tile_size * 0.06
        self.__get_rotation(current_time, LOCK_SHAKE_TIME)
        # if tile_data["locked"] or len(self.value) == 1:
        if current_time - self.__tile_data["click_time"] <= TRANSITION_TIME and is_type_transition():
            double_value = self.value if len(self.value) == 2 else self.__tile_data["previous_tile"]
            single_value = self.value[0] if len(self.value) == 1 else self.__tile_data["previous_tile"][0]
            multicolor:pygame.Surface = get_multicolor(double_value, double_value)
            full_color:pygame.Surface = get_full_color(single_value, single_value)
            color_ratio = self.__get_color_ratio(current_time, TRANSITION_TIME, self.__tile_data["click_time"])
            if len(self.value) == 2: color_ratio = 1 - color_ratio
            full_color.set_alpha(255 * color_ratio)
            multicolor.blit(full_color, (0, 0))
            button_surface = multicolor
        elif len(self.value) == 1: button_surface = get_full_color(single_color_to_int(self.value), single_color_to_int(self.__tile_data["previous_tile"]))
        else: button_surface = get_multicolor(self.value, self.__tile_data["previous_tile"])
        if len(self.value) == 1:
            button_surface.blit(self.__draw_shadow(padding_size, shadow_radius), (0, 0))
        return button_surface

    def __get_rotation(self, current_time:float, time:float) -> None:
        self.rotation = 0
        if self.__tile_data["click_type"] == "locked":
            click_time = self.__tile_data["click_time"] if isinstance(self.__tile_data["click_time"], float) else self.__tile_data["click_time"][0]
            if current_time - click_time <= time:
                self.rotation = math.radians(Animations.animate(Animations.wiggle, time, Bezier.linear_bezier, current_time - self.__tile_data["click_time"])) # ANIMATION
        self.sin_rotation = math.sin(self.rotation)
        self.cos_rotation = math.cos(self.rotation)

    COLORS = {
        (0, False): Colors.tile0,
        (0, True): Colors.tile0,
        (1, False): Colors.tile1_odd,
        (1, True): Colors.tile1_even,
        (2, False): Colors.tile2_odd,
        (2, True): Colors.tile2_even,
        (3, False): Colors.tile3_odd,
        (3, True): Colors.tile3_even,
        (4, False): Colors.tile4_odd,
        (4, True): Colors.tile4_even
    }
    def __blend_colors(self, color1:pygame.Color, color2:pygame.Color, ratio:float) -> pygame.Color:
        if ratio == 1.0: return color1
        elif ratio == 0.0: return color2
        color1_r, color1_g, color1_b = color1.r, color1.g, color1.b
        color2_r, color2_g, color2_b = color2.r, color2.g, color2.b
        new_r = int(color1_r * ratio + color2_r * (1 - ratio))
        new_g = int(color1_g * ratio + color2_g * (1 - ratio))
        new_b = int(color1_b * ratio + color2_b * (1 - ratio))
        return pygame.Color(new_r, new_g, new_b)
    def __get_color_ratio(self, current_time:float, time:float, click_time:float) -> float:
        '''Gets the ratio that two colors should be averaged together with'''
        color_time = (current_time - click_time) / time
        ratio = Bezier.ease_out(0.0, 1.0, color_time)
        return ratio

    def __get_tile_color(self, value:int|None=None) -> pygame.Color:
        value = self.value if value is None else value
        return Tile.COLORS[(value, self.is_even)]

    def __draw_body(self, padding_size:float, border_radius:float, color:pygame.Color) -> pygame.Surface:
        # ROUNDED BORDER
        button_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        circle_pos = self.__position(padding_size + border_radius, padding_size + border_radius)
        pygame.draw.circle(button_surface, color, circle_pos, border_radius, 0, *self.__get_circle_quarters(False, True, False, False))
        circle_pos = self.__position(self.size - (padding_size + border_radius) + 1, padding_size + border_radius)
        pygame.draw.circle(button_surface, color, circle_pos, border_radius, 0, *self.__get_circle_quarters(True, False, False, False))
        circle_pos = self.__position(padding_size + border_radius, self.size - (padding_size + border_radius))
        pygame.draw.circle(button_surface, color, circle_pos, border_radius, 0, *self.__get_circle_quarters(False, False, True, False))
        circle_pos = self.__position(self.size - (padding_size + border_radius), self.size - (padding_size + border_radius))
        pygame.draw.circle(button_surface, color, circle_pos, border_radius, 0, *self.__get_circle_quarters(False, False, False, True))

        # CENTER PORTION OF TILE
        polygon_sequence = [
            self.__position(padding_size + border_radius, padding_size),
            self.__position(padding_size + border_radius, padding_size + border_radius),
            self.__position(padding_size, padding_size + border_radius),
            self.__position(padding_size, self.size - (padding_size + border_radius)),
            self.__position(padding_size + border_radius, self.size - (padding_size + border_radius)),
            self.__position(padding_size + border_radius, self.size - padding_size),
            self.__position(self.size - (padding_size + border_radius), self.size - padding_size),
            self.__position(self.size - (padding_size + border_radius), self.size - (padding_size + border_radius)),
            self.__position(self.size - padding_size, self.size - (padding_size + border_radius)),
            self.__position(self.size - padding_size, padding_size + border_radius),
            self.__position(self.size - (padding_size + border_radius), padding_size + border_radius),
            self.__position(self.size - (padding_size + border_radius), padding_size)
        ]
        pygame.draw.polygon(button_surface, color, polygon_sequence)
        return button_surface
    
    def __draw_multicolor(self, padding_size:float, value:list[int], previous_value:list[int], sections:int, current_time:float, mask:pygame.Surface) -> pygame.Surface:
        colors:list[pygame.Color] = []
        COLOR_RESTRICTIONS = (0.0625, 0.25) # (0.125, 0.25)
        for index in range(sections):
            is_in_previous = index + 1 in previous_value
            is_in_current = index + 1 in value
            is_transitioning = ((is_in_previous and not is_in_current) or (not is_in_previous and is_in_current)) and current_time - self.__tile_data["click_time_sections"][index] <= TRANSITION_TIME
            full_color = self.__get_tile_color(index + 1)
            empty_color = self.__get_tile_color(0)
            if is_transitioning:
                color_ratio = self.__get_color_ratio(current_time, TRANSITION_TIME, self.__tile_data["click_time_sections"][index])
                # print(color_ratio, self.__tile_data["click_time_sections"], index)
                if index + 1 in value: color_ratio = Bezier.linear_bezier(COLOR_RESTRICTIONS[0], COLOR_RESTRICTIONS[1], color_ratio)
                else: color_ratio = Bezier.linear_bezier(COLOR_RESTRICTIONS[1], COLOR_RESTRICTIONS[0], color_ratio)
            else:
                if index + 1 in value: color_ratio = COLOR_RESTRICTIONS[1]
                else: color_ratio = COLOR_RESTRICTIONS[0]
            color = self.__blend_colors(full_color, empty_color, color_ratio)
            colors.append(color)
        button_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        button_surface.fill(Colors.tile0)
        directions = [(math.tau / sections) * (index - 1) + (math.pi / 2) + (math.pi / sections) for index in range(sections + 1)]
        direction = directions[0]
        line_endpoints:list[tuple[float,float]] = [] # remember to allow for lines to be drawn
        x, y = -1 * self.size * math.cos(direction), -1 * self.size * math.sin(direction)
        center = self.size / 2
        for index in range(sections):
            line_endpoints.append((x, y))
            next_direction = directions[index + 1]
            next_x, next_y = -1 * self.size * math.cos(next_direction), -1 * self.size * math.sin(next_direction)
            center_angle = (direction + next_direction) / 2
            center_x, center_y = -1 * self.size * math.cos(center_angle), -1 * self.size * math.sin(center_angle)
            polygon_sequence = [
                self.__position(center + x, center + y),
                self.__position(center + center_x, center + center_y),
                self.__position(center + next_x, center + next_y),
                self.__position(center, center)
            ]
            pygame.draw.polygon(button_surface, colors[index], polygon_sequence)
            direction = next_direction
            x, y = next_x, next_y
        for x, y in line_endpoints:
            pygame.draw.line(button_surface, Colors.tile0, (center, center), (center + x, center + y), int(padding_size))
            
        mask_inverted = pygame.Surface(mask.get_size(), pygame.SRCALPHA)
        mask_inverted.fill(pygame.Color(255, 255, 255))
        mask_inverted.blit(mask, (0, 0))
        mask_inverted.set_colorkey(pygame.Color(0, 0, 0))
        button_surface.blit(mask_inverted, (0, 0))
        button_surface.set_colorkey(pygame.Color(255, 255, 255))
        output_surface = pygame.Surface(button_surface.get_size(), pygame.SRCALPHA)
        output_surface.blit(button_surface, (0, 0)) # get rid of mask color
        return output_surface

    def __draw_shadow(self, padding_size:float, shadow_radius:float) -> pygame.Surface:
        shadow_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surface, Colors.tile_shadow, self.__position(padding_size + shadow_radius, self.size - (padding_size + shadow_radius)), shadow_radius, 0, *self.__get_circle_quarters(False, True, True, False))
        pygame.draw.circle(shadow_surface, Colors.tile_shadow, self.__position(self.size - (padding_size + shadow_radius), self.size - (padding_size + shadow_radius)), shadow_radius, 0, *self.__get_circle_quarters(True, False, False, True))
        polygon_sequence = [
            self.__position(padding_size + shadow_radius, self.size - (padding_size + shadow_radius * 2)),
            self.__position(padding_size + shadow_radius, self.size - padding_size),
            self.__position(self.size - (padding_size + shadow_radius), self.size - padding_size),
            self.__position(self.size - (padding_size + shadow_radius), self.size - (padding_size + shadow_radius * 2))
        ]
        pygame.draw.polygon(shadow_surface, Colors.tile_shadow, polygon_sequence)
        return shadow_surface
