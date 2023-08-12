import pygame

import UI.Button as Button
import UI.ButtonPanel as ButtonPanel
import UI.Colors as Colors
import UI.Drawable as Drawable
import UI.Fonts as Fonts
import Utilities.Animation as Animation
import Utilities.Bezier as Bezier

FADE_TIME = 0.1

class SettingsMenu(Drawable.Drawable):
    def __init__(self, window_size:tuple[int,int], surface:pygame.Surface|None=None, restore_objects:list[tuple[Drawable.Drawable,int]]|None=None, children:list[Drawable.Drawable]|None=None) -> None:
        if children is None: children = []
        self.opacity = Animation.Animation(1.0, 0.0, FADE_TIME, Bezier.ease_in)
        self.is_closing = False
        self.window_size = window_size
        self.display_size = (self.window_size[0] * 0.75, self.window_size[1])
        self.position = ((self.window_size[0] - self.display_size[0]) / 2, (self.window_size[1] - self.display_size[1]) / 2)
        additional_children = [
            self.get_title(),
            ButtonPanel.ButtonPanel([("close.png", (self.button_close,))], self.position[1] + 0.9 * self.display_size[1], self.window_size[1], self.position[0], self.position[0] + self.display_size[0])
            ]
        super().__init__(surface, self.position, restore_objects, children + additional_children)
    
    def get_title(self) -> Drawable.Drawable:
        font = Fonts.get_fitted_font("Settings", "molle", 90, self.display_size[0], self.display_size[1] / 10)
        font_surface = font.render("Settings", True, Colors.font)
        font_size = font_surface.get_size()
        position = (self.position[0] + (self.display_size[0] - font_size[0]) / 2, self.position[1] + (self.display_size[1] / 10 - font_size[1]) / 2)
        return Drawable.Drawable(font_surface, position)

    def button_close(self) -> None:
        self.opacity.set(0.0)
        self.is_closing = True
        for child in self.children:
            if isinstance(child, Button.Button): child.enabled = False
    
    def display(self) -> pygame.Surface:
        self.set_alpha(255 * self.opacity.get())
        return super().display()

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[int,int]) -> list[tuple[Drawable.Drawable]]|None:
        if self.is_closing and self.opacity.get() == 0.0:
            self.should_destroy = True
