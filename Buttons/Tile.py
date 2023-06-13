import math
import pygame

import Buttons.Button as Button
import Colors
import Utilities.Animations as Animations
import Utilities.Bezier as Bezier

class Tile(Button.Button):
    def __init__(self, size:int=160, tile_type:int=0, is_even:bool=False) -> None:
        self.size = size
        self.tile_type = tile_type
        self.is_even = is_even
        super().__init__(self.new_surface())
    
    def new_surface(self, ticks:int=0) -> pygame.Surface:
        COLORS = {
            (0, False): Colors.tile0,
            (0, True): Colors.tile0,
            (1, False): Colors.tile1_odd,
            (1, True): Colors.tile1_even,
            (2, False): Colors.tile2_odd,
            (2, True): Colors.tile2_even,
        }
        def position(x:float, y:float) -> tuple[float, float]:
            if rotation == 0: return x, y
            offset = self.size / 2
            new_x = (x - offset) * cos_rotation - (y - offset) * sin_rotation + offset
            new_y = (x - offset) * sin_rotation + (y - offset) * cos_rotation + offset
            return new_x, new_y
        def get_circle_quarters(top_right:bool, top_left:bool, bottom_left:bool, bottom_right:bool) -> tuple[bool,bool,bool,bool]:
            if rotation != 0: return True, True, True, True
            else: return top_right, top_left, bottom_left, bottom_right
        if self.tile_type != 0: rotation = math.radians(Animations.animate(Animations.wiggle, 0.5, Bezier.ease, ticks/60)) # ANIMATION
        else: rotation = 0
        sin_rotation = math.sin(rotation)
        cos_rotation = math.cos(rotation)
        button_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        padding_size = 0.04 * self.size
        tile_size = self.size - (padding_size * 2)
        border_radius = self.size * 0.1
        shadow_radius = tile_size * 0.06
        color = COLORS[(self.tile_type, self.is_even)]
        
        # ROUNDED BORDER
        circle_pos = position(padding_size + border_radius, padding_size + border_radius)
        pygame.draw.circle(button_surface, color, circle_pos, border_radius, 0, *get_circle_quarters(False, True, False, False))
        circle_pos = position(self.size - (padding_size + border_radius) + 1, padding_size + border_radius)
        pygame.draw.circle(button_surface, color, circle_pos, border_radius, 0, *get_circle_quarters(True, False, False, False))
        circle_pos = position(padding_size + border_radius, self.size - (padding_size + border_radius))
        pygame.draw.circle(button_surface, color, circle_pos, border_radius, 0, *get_circle_quarters(False, False, True, False))
        circle_pos = position(self.size - (padding_size + border_radius), self.size - (padding_size + border_radius))
        pygame.draw.circle(button_surface, color, circle_pos, border_radius, 0, *get_circle_quarters(False, False, False, True))

        # CENTER PORTION OF TILE
        polygon_sequence = [
            position(padding_size + border_radius, padding_size),
            position(padding_size + border_radius, padding_size + border_radius),
            position(padding_size, padding_size + border_radius),
            position(padding_size, self.size - (padding_size + border_radius)),
            position(padding_size + border_radius, self.size - (padding_size + border_radius)),
            position(padding_size + border_radius, self.size - padding_size),
            position(self.size - (padding_size + border_radius), self.size - padding_size),
            position(self.size - (padding_size + border_radius), self.size - (padding_size + border_radius)),
            position(self.size - padding_size, self.size - (padding_size + border_radius)),
            position(self.size - padding_size, padding_size + border_radius),
            position(self.size - (padding_size + border_radius), padding_size + border_radius),
            position(self.size - (padding_size + border_radius), padding_size)
        ]
        pygame.draw.polygon(button_surface, color, polygon_sequence)

        # SHADOW
        if self.tile_type != 0:
            shadow_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.circle(shadow_surface, Colors.tile_shadow, position(padding_size + shadow_radius, self.size - (padding_size + shadow_radius)), shadow_radius, 0, *get_circle_quarters(False, True, True, False))
            pygame.draw.circle(shadow_surface, Colors.tile_shadow, position(self.size - (padding_size + shadow_radius), self.size - (padding_size + shadow_radius)), shadow_radius, 0, *get_circle_quarters(True, False, False, True))
            polygon_sequence = [
                position(padding_size + shadow_radius, self.size - (padding_size + shadow_radius * 2)),
                position(padding_size + shadow_radius, self.size - padding_size),
                position(self.size - (padding_size + shadow_radius), self.size - padding_size),
                position(self.size - (padding_size + shadow_radius), self.size - (padding_size + shadow_radius * 2))
            ]
            pygame.draw.polygon(shadow_surface, Colors.tile_shadow, polygon_sequence)
            button_surface.blit(shadow_surface, (0, 0))
            
        return button_surface
