from typing import Sequence

import pygame

import UI.Drawable as Drawable


class Enablable(Drawable.Drawable):
    def __init__(
        self,
        surface:pygame.Surface|None=None,
        position:tuple[float,float]|None=None,
        restore_objects:list[tuple[Drawable.Drawable,int]]|None=None,
        children:Sequence[Drawable.Drawable]|None=None,
        *,
        start_enabled:bool=True
    ) -> None:
        super().__init__(surface, position, restore_objects, children)
        self.start_enabled = start_enabled

    def disable(self) -> None:
        self.enabled = False
        for child in self.children:
            if isinstance(child, Enablable): child.disable()

    def enable(self) -> None:
        self.enabled = True
        for child in self.children:
            if isinstance(child, Enablable): child.enable()
