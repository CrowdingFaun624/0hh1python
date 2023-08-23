import math

import pygame

import UI.Colors as Colors
import UI.Drawable as Drawable
import Utilities.Animation as Animation
import Utilities.Bezier as Bezier

LOCK_SHAKE_TIME = 0.5 # when locked tile is interacted with
TRANSITION_TIME = 0.2 # from one color to another

def get_color_name(value:int, parity:bool) -> str:
    color_string = "tile.%s" % str(value)
    if value != 0:
        color_string += "_" + {False: "odd", True: "even"}[parity]
    if not Colors.is_exist(color_string): raise ValueError("Unsupported color/parity %i %b (%s)" % (value, parity, color_string))
    return color_string

class Tile(Drawable.Drawable):
    def __init__(self, index:int, size:int, value:int|list[int], is_even:bool, colors:int, current_time:float, start_progress:float=1.0, is_locked:bool=False, can_modify:bool=True, show_lock:bool=False, lock_surface:pygame.Surface|None=None, mode:str|None=None) -> None:
        self.index = index
        self.size = size
        self.value = value
        self.is_even = is_even
        self.colors = colors # how many colors the board has
        self.is_locked = is_locked

        self.click_time = 0.0
        self.click_time_locked = 0.0
        if colors == 2:
            current_color = Colors.get(get_color_name(value, is_even))
        else:
            current_color = Colors.get(get_color_name(value[0], is_even)) if len(value) == 1 else Colors.get(get_color_name(0, is_even))
            self.section_opacities:list[Animation.Animation] = [Animation.Animation(cur := (self.get_section_opacity(color) if color in value else 0.0), cur, TRANSITION_TIME, Bezier.ease_out) for color in range(1, colors + 1)]
            self.multicolor_transition = Animation.Animation(float(self.is_locked), float(self.is_locked), TRANSITION_TIME, Bezier.ease_out)
        color_tuple = (current_color.r, current_color.g, current_color.b)
        self.color = Animation.MultiAnimation(color_tuple, color_tuple, TRANSITION_TIME, Bezier.ease_out)

        self.mouse_over_time = 0.0
        self.mouse_over_start = 0.0
        self.is_mousing_over = False
        self.click_type = None
        self.is_mousing_over = False
        self.can_modify = can_modify
        self.show_lock = False
        self.lock_surface = lock_surface
        self.is_highlighted = False
        self.highlight_time = None
        self.highlight_pulse_opacity = 0.0
        self.highlight_transition_opacity = Animation.Animation(0.0, 0.0, TRANSITION_TIME, Bezier.ease_out)
        
        self.transition_progress = start_progress
        self.multicolor_brightness_progress = [0.0] * self.colors; self.multicolor_brightness_progress_eased = [0.0] * self.colors

        self.current_surface_conditions:list[any] = None
        self.last_tick_time = current_time
        self.rotation = 0.0
        self.multicolor_mask = self.__get_multicolor_mask()
        self.multicolor_mask_rotation = 0.0
        self.highlight_mask = self.__get_highlight_mask()
        self.highlight_mask_rotation = 0.0
        self.mode = mode # used to determine which function to use when reloading.
        super().__init__()
        self.reload_for_board(None, current_time, True)

    def set_value(self, value:int) -> None:
        self.value = value
        current_color = Colors.get(get_color_name(value, self.is_even))
        self.color.set((current_color.r, current_color.g, current_color.b))
    
    def __set_multicolor_transition_target(self) -> float:
        if self.colors == 2: return
        elif len(self.value) != 1: value = 0.0
        elif not self.can_modify: value = 1.0
        elif self.is_mousing_over: value = 0.0
        else: value = 1.0
        self.multicolor_transition.set(value)

    def start_mousing_over(self, current_time:float) -> None:
        self.mouse_over_start = current_time
        self.is_mousing_over = True
        self.__set_multicolor_transition_target() # self.multicolor_transition.set(0.0)
    def stop_mousing_over(self, current_time:float) -> None:
        self.mouse_over_time = current_time
        self.is_mousing_over = False
        self.__set_multicolor_transition_target() # self.multicolor_transition.set(1.0)

    def set_value_multi(self, color:int, value:bool) -> None:
        if value:
            if color not in self.value:
                self.value.append(color)
                self.value.sort()
        else:
            if color in self.value:
                self.value.remove(color)
        for section in range(self.colors):
            self.section_opacities[section].set(self.get_section_opacity(section + 1))
        if len(self.value) == 1: self.__set_multicolor_transition_target() # self.multicolor_transition.set(1.0)
        else: self.multicolor_transition.set(0.0)
        if len(self.value) == 1: current_color = Colors.get(get_color_name(self.value[0], self.is_even))
        else: current_color = Colors.get(get_color_name(0, self.is_even))
        self.color.set((current_color.r, current_color.g, current_color.b))
    
    def highlight(self, current_time:float) -> None:
        self.is_highlighted = True
        self.highlight_time = current_time
        self.highlight_transition_opacity.set(1.0)
    def unhighlight(self) -> None:
        self.is_highlighted = False
        self.highlight_transition_opacity.set(0.0)

    def get_section_opacity(self, color:int) -> float:
        '''Will return the target color for the given section'''
        if len(self.value) == 1:
            if self.value[0] == color: return 0.75
            else: return 0.0625
        else:
            if color in self.value: return 0.25
            else: return 0.0625

    def get_conditions(self, current_time:float) -> list[any]:
        '''Returns the conditions that the tile is in this frame.'''
        self.__get_rotation(current_time, LOCK_SHAKE_TIME)
        # if self.colors != 2:
        #     self.advance_transition_progress(current_time)
        #     self.advance_multicolor_brightness_progress(current_time)
        time_since_mouse_over = current_time - self.mouse_over_time
        time_since_mouse_start = current_time - self.mouse_over_start
        time_since_click = current_time - self.click_time
        conditions:list[any] = []
        conditions.append(self.rotation)
        color = self.color.get(current_time)
        conditions.append((65536 * int(color[0]) + 256 * int(color[1]) + int(color[2])))
        conditions.append(self.show_lock)
        conditions.append(self.highlight_pulse_opacity)
        if time_since_mouse_over <= TRANSITION_TIME: conditions.append(time_since_mouse_over)
        if time_since_mouse_start <= TRANSITION_TIME: conditions.append(time_since_mouse_start)
        if time_since_click <= TRANSITION_TIME: conditions.append(time_since_click)
        if self.is_highlighted: conditions.append(current_time - self.highlight_time)
        return conditions

    # def reload_for_loading(self, elapsed_time:float) -> pygame.Surface:
    #     self.__get_rotation_loading(elapsed_time)
    #     return self.__get_surface_normal(elapsed_time)

    def reload_for_board(self, required_surface_conditions:list[any], current_time:float, force_new:bool=False) -> None:
        '''Redraws the tile's surface if the conditions have changed.'''
        if force_new or self.current_surface_conditions != required_surface_conditions:
            # print("%s got new pants" % self.index, self.current_surface_conditions, required_surface_conditions)
            new_surface = self.get_new_surface(current_time)
            self.surface = new_surface
            self.current_surface_conditions = required_surface_conditions
            self.surface = new_surface

    def reload(self, current_time:float) -> None:
        match self.mode:
            case "board": self.reload_for_board(None, 0.0, True)
            # case "loading": self.reload_for_loading()
            case "static": self.surface = self.__get_surface_normal(current_time)
        super().reload()

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

    def __get_highlight(self, current_time:float) -> pygame.Surface:
        if self.highlight_mask_rotation != self.rotation: self.highlight_mask = self.__get_highlight_mask()
        self.highlight_pulse_opacity = Animation.animate(Animation.flash, 2.0, Bezier.ease_in_out, current_time - self.highlight_time)
        opacity = self.highlight_pulse_opacity
        opacity *= self.highlight_transition_opacity.get(current_time)
        self.highlight_mask.set_alpha(opacity * 255)
        return self.highlight_mask

    def __get_surface_normal(self, current_time:float) -> pygame.Surface:
        color = self.color.get(current_time)
        color = pygame.Color(int(color[0]), int(color[1]), int(color[2]))
        
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
        if self.highlight_transition_opacity.get(current_time) != 0.0:
            button_surface.blit(self.__get_highlight(current_time), (0, 0))
        return button_surface

    def __get_surface_multicolor(self, current_time:float) -> pygame.Surface:
        def get_multicolor() -> pygame.Surface:
            return self.__draw_multicolor(padding_size, self.colors, current_time)
        def get_full_color() -> pygame.Surface:
            color = self.color.get(current_time)
            color = pygame.Color(int(color[0]), int(color[1]), int(color[2]))
            return self.__draw_body(padding_size, border_radius, color)

        padding_size = 0.04 * self.size
        tile_size = self.size - (padding_size * 2)
        border_radius = self.size * 0.1
        shadow_radius = tile_size * 0.06
        transition_progress = self.multicolor_transition.get(current_time)
        if transition_progress == 1.0: button_surface = get_full_color()
        elif transition_progress == 0.0: button_surface = get_multicolor()
        else:
            full_color = get_full_color()
            multicolor = get_multicolor()

            full_color.set_alpha(255 * transition_progress)
            multicolor.blit(full_color, (0, 0))
            button_surface = multicolor
        if len(self.value) == 1:
            button_surface.blit(self.__draw_shadow(padding_size, shadow_radius), (0, 0))
        if self.show_lock and self.lock_surface is not None:
            lock_surface, position = self.__get_lock()
            button_surface.blit(lock_surface, position)
        if self.highlight_transition_opacity.get(current_time) != 0.0:
            button_surface.blit(self.__get_highlight(current_time), (0, 0))
        return button_surface

    def __get_rotation(self, current_time:float, time:float) -> None:
        self.rotation = 0
        if current_time - self.click_time_locked <= time:
            self.rotation = math.radians(Animation.animate(Animation.wiggle, time, Bezier.ease, current_time - self.click_time_locked)) # ANIMATION
        self.sin_rotation = math.sin(self.rotation)
        self.cos_rotation = math.cos(self.rotation)
    def __get_rotation_loading(self, elapsed_time:float) -> None:
        self.rotation = math.radians(Animation.animate(Animation.wiggle, 2.0, Bezier.ease, elapsed_time, True))
        self.sin_rotation = math.sin(self.rotation)
        self.cos_rotation = math.cos(self.rotation)

    def __blend_colors(self, color1:pygame.Color, color2:pygame.Color, ratio:float) -> pygame.Color:
        if ratio == 1.0: return color1
        elif ratio == 0.0: return color2
        color1_r, color1_g, color1_b = color1.r, color1.g, color1.b
        color2_r, color2_g, color2_b = color2.r, color2.g, color2.b
        new_r = int(color1_r * ratio + color2_r * (1 - ratio))
        new_g = int(color1_g * ratio + color2_g * (1 - ratio))
        new_b = int(color1_b * ratio + color2_b * (1 - ratio))
        return pygame.Color(new_r, new_g, new_b)

    def __get_tile_color(self, value:int|None=None) -> pygame.Color:
        value = self.value if value is None else value
        return Colors.get(get_color_name(value, self.is_even))

    def __get_multicolor_mask(self) -> pygame.Surface:
        padding_size = 0.04 * self.size
        border_radius = self.size * 0.1
        mask = self.__draw_body(padding_size, border_radius, pygame.Color(0, 0, 0))
        mask_inverted = pygame.Surface(mask.get_size(), pygame.SRCALPHA)
        mask_inverted.fill(pygame.Color(255, 255, 255))
        mask_inverted.blit(mask, (0, 0)) # TODO: cache mask_inverted too; make sure to copy though
        mask_inverted.set_colorkey(pygame.Color(0, 0, 0))
        return mask_inverted

    def __get_highlight_mask(self) -> pygame.Surface:
        padding_size = 0.04 * self.size
        border_radius = self.size * 0.1
        mask_surface = pygame.Surface((self.size, self.size))
        color = Colors.get("tile.highlight")
        mask_color = Colors.get_non_conflicting_colors([color])
        mask_surface.fill(mask_color)
        base_surface = self.__draw_body(padding_size, border_radius, color)
        mask_surface.blit(base_surface, (0, 0))
        if border_radius > 3: # rounded interior
            interior_surface = self.__draw_body(padding_size + 3, border_radius, mask_color)
        else: # square interior
            interior_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            polygon_sequence = [
                self.__position(padding_size + 3, padding_size + 3),
                self.__position(self.size - (padding_size + 3), padding_size + 3),
                self.__position(self.size - (padding_size + 3), self.size - (padding_size + 3)),
                self.__position(padding_size + 3, self.size - (padding_size + 3))
            ]
            pygame.draw.polygon(interior_surface, mask_color, polygon_sequence)
        mask_surface.blit(interior_surface, (0, 0))
        mask_surface.set_colorkey(mask_color)
        return mask_surface

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
            full_color = self.__get_tile_color(index + 1)
            empty_color = self.__get_tile_color(0)
            color = self.__blend_colors(full_color, empty_color, self.section_opacities[index].get(current_time))
            colors.append(color)
        button_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        button_surface.fill(Colors.get("tile.0"))
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
            pygame.draw.line(button_surface, Colors.get("tile.0"), self.__position(center, center), self.__position(center + x, center + y), int(padding_size))
        
        if self.multicolor_mask_rotation != self.rotation: self.multicolor_mask = self.__get_multicolor_mask()
        button_surface.blit(self.multicolor_mask, (0, 0))
        button_surface.set_colorkey(pygame.Color(255, 255, 255))
        output_surface = pygame.Surface(button_surface.get_size(), pygame.SRCALPHA)
        output_surface.blit(button_surface, (0, 0)) # get rid of mask color
        return output_surface

    def __draw_shadow(self, padding_size:float, shadow_radius:float) -> pygame.Surface:
        shadow_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surface, Colors.get("tile.shadow"), self.__position(padding_size + shadow_radius, self.size - (padding_size + shadow_radius)), shadow_radius, 0, *self.__get_circle_quarters(False, True, True, False))
        pygame.draw.circle(shadow_surface, Colors.get("tile.shadow"), self.__position(self.size - (padding_size + shadow_radius), self.size - (padding_size + shadow_radius)), shadow_radius, 0, *self.__get_circle_quarters(True, False, False, True))
        polygon_sequence = [
            self.__position(padding_size + shadow_radius, self.size - (padding_size + shadow_radius * 2)),
            self.__position(padding_size + shadow_radius, self.size - padding_size),
            self.__position(self.size - (padding_size + shadow_radius), self.size - padding_size),
            self.__position(self.size - (padding_size + shadow_radius), self.size - (padding_size + shadow_radius * 2))
        ]
        pygame.draw.polygon(shadow_surface, Colors.get("tile.shadow"), polygon_sequence)
        return shadow_surface
