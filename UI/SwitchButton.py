import time
from collections.abc import Callable

import pygame

import UI.Button as Button
import UI.Colors as Colors
import UI.Drawable as Drawable
import Utilities.Animation as Animation
import Utilities.Bezier as Bezier

TRANSITION_TIME = 0.125
WIDTH = 75
HEIGHT = 50
INNER_RADIUS = 10
INNER_BORDER_RADIUS = 1
OUTER_RADIUS=15
OUTER_BORDER_RADIUS = 1

class SwitchButton(Button.Button):
    def __init__(self, position:tuple[int, int], restore_objects:list[tuple[Drawable.Drawable,int]]|None=None, children:list[Drawable.Drawable]|None=None, toggle_on_action:tuple[Callable[[],list[tuple[Drawable.Drawable,int]]|None],list,dict[str,any]]|list|None=None, toggle_off_action:tuple[Callable[[],list[tuple[Drawable.Drawable,int]]|None],list,dict[str,any]]|list|None=None, start_toggled:bool=False, start_enabled:bool=True) -> None:
        if toggle_on_action is None: self.toggle_on_action = []
        elif isinstance(toggle_on_action, list): self.toggle_on_action = toggle_on_action
        else: self.toggle_on_action = [toggle_on_action]
        if toggle_off_action is None: self.toggle_off_action = []
        elif isinstance(toggle_off_action, list): self.toggle_off_action = toggle_off_action
        else: self.toggle_off_action = [toggle_off_action]
        self.toggled = start_toggled
        self.toggle_time = 0.0
        self.animation = Animation.Animation(float(start_toggled), float(start_toggled), TRANSITION_TIME, Bezier.ease)
        self.color = Animation.MultiAnimation(self.__get_color(), self.__get_color(), TRANSITION_TIME, Bezier.ease)
        super().__init__(self.get_new_surface(time.time()), position, restore_objects, children, (self.toggle,), None, start_enabled)

    def __get_color(self) -> tuple[int,int,int]:
        if self.toggled: color = Colors.get("switch_button.inner_on")
        else: color = Colors.get("switch_button.inner_off")
        return color.r, color.g, color.b

    def toggle(self) -> list[tuple[Drawable.Drawable,int]]|None:
        self.toggle_time = time.time()
        return_stuff = []
        if self.toggled:
            self.animation.set(0.0)
            self.toggled = False
            self.color.set(self.__get_color())
            return_stuff = self.call(self.toggle_off_action)
        else:
            self.animation.set(1.0)
            self.toggled = True
            self.color.set(self.__get_color())
            return_stuff = self.call(self.toggle_on_action)
        return return_stuff
    
    def display(self) -> pygame.Surface:
        current_time = time.time()
        if current_time - self.toggle_time <= TRANSITION_TIME:
            self.surface = self.get_new_surface(current_time)
        return self.surface

    def reload(self, current_time:float) -> None:
        self.surface = self.get_new_surface(time.time())
        return super().reload(current_time)

    def get_new_surface(self, current_time:float) -> pygame.Surface:
        surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        inner_color = self.color.get()
        outer_color = Colors.get("switch_button.outer")
        border_color = Colors.get("switch_button.border")
        switch_color = Colors.get("switch_button.switch")
        pygame.draw.rect(surface, inner_color, pygame.Rect(OUTER_RADIUS, HEIGHT / 2 - INNER_RADIUS, WIDTH - (OUTER_RADIUS * 2), INNER_RADIUS * 2))
        pygame.draw.rect(surface, border_color, pygame.Rect(OUTER_RADIUS - INNER_BORDER_RADIUS, HEIGHT / 2 - INNER_RADIUS, WIDTH - (OUTER_RADIUS * 2) + (2 * INNER_BORDER_RADIUS), INNER_RADIUS * 2), INNER_BORDER_RADIUS)
        pygame.draw.circle(surface, inner_color, (OUTER_RADIUS, HEIGHT / 2), INNER_RADIUS, 0, False, True, True, False)
        pygame.draw.circle(surface, border_color, (OUTER_RADIUS, HEIGHT / 2), INNER_RADIUS, INNER_BORDER_RADIUS, False, True, True, False)
        pygame.draw.circle(surface, inner_color, (WIDTH - OUTER_RADIUS, HEIGHT / 2), INNER_RADIUS, 0, True, False, False, True)
        pygame.draw.circle(surface, border_color, (WIDTH - OUTER_RADIUS, HEIGHT / 2), INNER_RADIUS, INNER_BORDER_RADIUS, True, False, False, True)
        progress = self.animation.get(current_time)
        x_position = Bezier.linear_bezier(OUTER_RADIUS, WIDTH - OUTER_RADIUS, progress)
        pygame.draw.circle(surface, switch_color, (x_position, HEIGHT / 2), OUTER_RADIUS)
        pygame.draw.circle(surface, border_color, (x_position, HEIGHT / 2), OUTER_RADIUS, OUTER_BORDER_RADIUS)
        return surface
