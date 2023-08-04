import math

import pygame

import UI.Colors as Colors
import Utilities.Animations as Animations
import Utilities.Bezier as Bezier

LOCK_SHAKE_TIME = 0.5 # when locked tile is interacted with
TRANSITION_TIME = 0.2 # from one color to another

class Tile():
    def __init__(self, index:int, size:int, value:int|list[int], is_even:bool, colors:int, current_time:float, start_progress:float=1.0, is_locked:bool=False, can_modify:bool=True, show_lock:bool=False, lock_surface:pygame.Surface|None=None) -> None:
        self.index = index
        self.size = size
        self.value = value
        self.is_even = is_even
        self.colors = colors # how many colors the board has

        self.click_time = 0.0
        self.click_time_sections:list[float] = [0.0] * self.colors
        self.mouse_over_time = 0.0
        self.mouse_over_start = 0.0
        self.is_mousing_over = False
        self.click_type = None
        self.previous_value:list[int]|int|None = list(range(1, self.colors + 1)) if colors > 2 else None
        self.is_mousing_over = False
        self.is_locked = is_locked
        self.can_modify = can_modify
        self.show_lock = False
        self.lock_surface = lock_surface
        
        self.transition_progress = start_progress
        self.multicolor_brightness_progress = [0.0] * self.colors; self.multicolor_brightness_progress_eased = [0.0] * self.colors

        self.surface = None
        self.current_surface_conditions:list[any] = None
        self.last_tick_time = current_time
        self.rotation = 0.0
        self.mask = self.__draw_body(0.04 * self.size, self.size * 0.1, pygame.Color(0, 0, 0)) # for multicolor

    def tick(self, current_time:float) -> list[any]:
        '''Returns the conditions that the tile is in this frame.'''
        self.__get_rotation(current_time, LOCK_SHAKE_TIME)
        if self.colors != 2:
            self.advance_transition_progress(current_time)
            self.advance_multicolor_brightness_progress(current_time)
        time_since_mouse_over = current_time - self.mouse_over_time
        time_since_mouse_start = current_time - self.mouse_over_start
        time_since_click = current_time - self.click_time
        conditions:list[any] = []
        conditions.append(self.rotation)
        conditions.append(self.transition_progress)
        conditions.append(self.show_lock)
        if time_since_mouse_over <= TRANSITION_TIME: conditions.append(time_since_mouse_over)
        if time_since_mouse_start <= TRANSITION_TIME: conditions.append(time_since_mouse_start)
        if time_since_click <= TRANSITION_TIME: conditions.append(time_since_click)
        return conditions

    def advance_transition_progress(self, current_time:float) -> None:
        '''Changes the transition progress according to the current state'''
        def get_direction() -> int:
            '''Returns 1 (toward full color) or -1 (toward multicolor)'''
            if len(self.value) != 1: return -1
            if self.is_mousing_over and not self.is_locked: return -1
            return 1
        direction = get_direction()
        amount = (current_time - self.last_tick_time) / TRANSITION_TIME
        self.transition_progress += direction * amount
        # there's no built in clamp function or anything wtf
        if self.transition_progress < 0.0: self.transition_progress = 0.0
        elif self.transition_progress > 1.0: self.transition_progress = 1.0
        self.transition_progress_eased = Bezier.ease_out(0.0, 1.0, self.transition_progress)
    
    def advance_multicolor_brightness_progress(self, current_time:float) -> None:
        '''Changes the multicolor brightness progress according to the current state'''
        def get_direction(index:int) -> int:
            '''Returns 1 (toward maximum brightness) or -1 (toward minimum brightness)'''
            if len(self.value) == 1 and index + 1 in self.value:
                return 1
            else: return -1
        for index in range(self.colors):
            direction = get_direction(index)
            amount = (current_time - self.last_tick_time) / TRANSITION_TIME
            self.multicolor_brightness_progress[index] += direction * amount
            if self.multicolor_brightness_progress[index] < 0.0: self.multicolor_brightness_progress[index] = 0.0
            elif self.multicolor_brightness_progress[index] > 1.0: self.multicolor_brightness_progress[index] = 1.0
            match direction:
                case -1:
                    self.multicolor_brightness_progress_eased[index] = Bezier.ease_out(0.0, 1.0, self.multicolor_brightness_progress[index])
                case 1:
                    self.multicolor_brightness_progress_eased[index] = 1 - Bezier.ease_out(0.0, 1.0, 1 - self.multicolor_brightness_progress[index])

    def display_loading(self, elapsed_time:float) -> pygame.Surface:
        self.__get_rotation_loading(elapsed_time)
        return self.__get_surface_normal(elapsed_time)

    def display(self, required_surface_conditions:list[any], current_time:float, force_new:bool=False) -> pygame.Surface:
        # if self.index == 17: print(self.index, self.transition_progress)
        if not force_new and self.current_surface_conditions == required_surface_conditions:
            return self.surface
        else:
            # print("%s got new pants" % self.index, self.current_surface_conditions, required_surface_conditions)
            new_surface = self.get_new_surface(current_time)
            self.surface = new_surface
            self.current_surface_conditions = required_surface_conditions
            return new_surface

    def get_new_surface(self, current_time:float) -> pygame.Surface:
        if self.colors == 2:
            return self.__get_surface_normal(current_time)
        else:
            return self.__get_surface_multicolor(current_time)

    def __position(self, x:float, y:float) -> tuple[float, float]:
        if self.rotation == 0: return x, y
        offset = self.size / 2
        new_x = (x - offset) * self.cos_rotation - (y - offset) * self.sin_rotation + offset
        new_y = (x - offset) * self.sin_rotation + (y - offset) * self.cos_rotation + offset
        return new_x, new_y
    def __get_circle_quarters(self, top_right:bool, top_left:bool, bottom_left:bool, bottom_right:bool) -> tuple[bool,bool,bool,bool]:
        if self.rotation != 0: return True, True, True, True
        else: return top_right, top_left, bottom_left, bottom_right

    def __get_lock(self) -> tuple[pygame.Surface,tuple[int,int]]:
        '''Returns the surface and position.'''
        if self.rotation != 0:
            lock_surface = pygame.transform.rotate(self.lock_surface, -math.degrees(self.rotation))
        else: lock_surface = self.lock_surface
        lock_size = lock_surface.get_size()
        corner = (int((self.size - lock_size[0]) / 2), int((self.size - lock_size[1]) / 2))
        return lock_surface, corner

    def __get_surface_normal(self, current_time) -> pygame.Surface:
        if self.click_type == "locked": color_ratio = 1.0
        else:
            if self.previous_value is None or current_time - self.click_time > TRANSITION_TIME:
                color_ratio = 1.0
            else: color_ratio = self.__get_color_ratio(current_time, TRANSITION_TIME, self.click_time)
        current_color = self.__get_tile_color()
        previous_color = self.__get_tile_color(self.previous_value)
        # print(self.value, self.previous_value, current_color, previous_color, color_ratio)
        color = self.__blend_colors(current_color, previous_color, color_ratio)
        
        padding_size = 0.04 * self.size
        tile_size = self.size - (padding_size * 2)
        border_radius = self.size * 0.1
        shadow_radius = tile_size * 0.06
        
        button_surface = self.__draw_body(padding_size, border_radius, color)
        if self.value != 0:
            button_surface.blit(self.__draw_shadow(padding_size, shadow_radius), (0, 0))
        if self.show_lock and self.lock_surface is not None:
            lock_surface, position = self.__get_lock()
            button_surface.blit(lock_surface, position)
        return button_surface

    def __get_surface_multicolor(self, current_time:float) -> pygame.Surface:
        def get_multicolor() -> pygame.Surface:
            return self.__draw_multicolor(padding_size, self.colors, current_time)
        def get_full_color(value:int, previous_value:int, click_time:float|None=None) -> pygame.Surface:
            if click_time is None: click_time = self.click_time
            if self.click_type == "locked": color_ratio = 1.0
            else:
                if previous_value is None or current_time - click_time > TRANSITION_TIME:
                    color_ratio = 1.0
                else: color_ratio = self.__get_color_ratio(current_time, TRANSITION_TIME, click_time)
            current_color = self.__get_tile_color(value)
            previous_color = self.__get_tile_color(previous_value)
            color = self.__blend_colors(current_color, previous_color, color_ratio)
            return self.__draw_body(padding_size, border_radius, color)

        def single_color_to_int(tile:list[int]) -> int:
            '''Returns the first item of the list, or 0 if it does not exist'''
            if len(tile) == 1: return tile[0]
            else: return 0
        padding_size = 0.04 * self.size
        tile_size = self.size - (padding_size * 2)
        border_radius = self.size * 0.1
        shadow_radius = tile_size * 0.06
        # self.__get_rotation(current_time, LOCK_SHAKE_TIME)
        if self.transition_progress_eased == 1.0: button_surface = get_full_color(single_color_to_int(self.value), single_color_to_int(self.previous_value))
        elif self.transition_progress_eased == 0.0: button_surface = get_multicolor()
        else:
            current_value_single = self.value[0] if len(self.value) == 1 else self.previous_value[0]
            full_color = get_full_color(current_value_single, current_value_single, 0.0)
            multicolor = get_multicolor()

            full_color.set_alpha(255 * self.transition_progress_eased)
            multicolor.blit(full_color, (0, 0))
            button_surface = multicolor
        if len(self.value) == 1:
            button_surface.blit(self.__draw_shadow(padding_size, shadow_radius), (0, 0))
        if self.show_lock and self.lock_surface is not None:
            lock_surface, position = self.__get_lock()
            button_surface.blit(lock_surface, position)
        return button_surface

    def __get_rotation(self, current_time:float, time:float) -> None:
        self.rotation = 0
        if self.click_type == "locked":
            if current_time - self.click_time <= time:
                self.rotation = math.radians(Animations.animate(Animations.wiggle, time, Bezier.ease, current_time - self.click_time)) # ANIMATION
        self.sin_rotation = math.sin(self.rotation)
        self.cos_rotation = math.cos(self.rotation)
    def __get_rotation_loading(self, elapsed_time:float) -> None:
        self.rotation = math.radians(Animations.animate(Animations.wiggle, 2.0, Bezier.ease, elapsed_time, True))
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
        circle_pos = self.__position(self.size - (padding_size + border_radius), padding_size + border_radius)
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
    
    def __draw_multicolor(self, padding_size:float, sections:int, current_time:float) -> pygame.Surface:
        colors:list[pygame.Color] = []
        for index in range(sections):
            color_restrictions = (0.0625, Bezier.linear_bezier(0.25, 0.75, self.multicolor_brightness_progress_eased[index]))
            is_in_previous = index + 1 in self.previous_value
            is_in_current = index + 1 in self.value
            is_transitioning = ((is_in_previous and not is_in_current) or (not is_in_previous and is_in_current)) and current_time - self.click_time_sections[index] <= TRANSITION_TIME
            full_color = self.__get_tile_color(index + 1)
            empty_color = self.__get_tile_color(0)
            if is_transitioning:
                color_ratio = self.__get_color_ratio(current_time, TRANSITION_TIME, self.click_time_sections[index])
                # print(color_ratio, self.click_time_sections, index)
                if index + 1 in self.value: color_ratio = Bezier.linear_bezier(color_restrictions[0], color_restrictions[1], color_ratio)
                else: color_ratio = Bezier.linear_bezier(color_restrictions[1], color_restrictions[0], color_ratio)
            else:
                if index + 1 in self.value: color_ratio = color_restrictions[1]
                else: color_ratio = color_restrictions[0]
            # print(color_ratio)
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
            pygame.draw.line(button_surface, Colors.tile0, self.__position(center, center), self.__position(center + x, center + y), int(padding_size))
            
        mask_inverted = pygame.Surface(self.mask.get_size(), pygame.SRCALPHA)
        mask_inverted.fill(pygame.Color(255, 255, 255))
        mask_inverted.blit(self.mask, (0, 0)) # TODO: cache mask_inverted too; make sure to copy though
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
