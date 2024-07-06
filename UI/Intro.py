import time
from typing import Callable

import pygame

import UI.Drawable as Drawable
import UI.Textures as Textures
import Utilities.Animation as Animation
import Utilities.Bezier as Bezier

FADE_IN_TIME = 0.25
FADE_OUT_TIME = 0.1

class Intro(Drawable.Drawable):
    def __init__(self, display_size:tuple[int,int], exit_function:Callable[["Intro"],list[tuple[Drawable.Drawable,int]]]) -> None:
        surface = pygame.transform.scale(Textures.get("logo_1024"), (min(display_size), min(display_size)))
        self.opacity = Animation.Animation(1.0, 0.0, FADE_IN_TIME, Bezier.ease_in)
        self.exit_function = exit_function
        super().__init__(surface, (0, 0))
    
    def display(self) -> pygame.Surface:
        self.surface.set_alpha(255 * self.opacity.get())
        return self.surface

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[int,int]) -> list[tuple[Drawable.Drawable]]|None:
        current_time = time.time()
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.opacity.set(0.0, FADE_OUT_TIME, current_time)
        if self.opacity.is_finished(current_time) and self.opacity.get(current_time) == 0.0:
            self.should_destroy = True
            return self.exit_function(self)
