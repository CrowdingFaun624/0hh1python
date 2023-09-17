import time
from typing import Callable, Any

import pygame

import UI.Button as Button
import UI.Colors as Colors
import UI.Drawable as Drawable
import Utilities.Animation as Animation
import Utilities.Bezier as Bezier

TRANSITION_TIME = 0.2
WIDTH = 50
INNER_RADIUS = 10
INNER_BORDER_RADIUS = 1
OUTER_RADIUS=15
OUTER_BORDER_RADIUS = 1
VALID_MOUSE_BUTTONS = [1]

class Slider(Button.Button):
    def __init__(self, position:tuple[int, int], length:int, is_vertical:bool=False, actions:list[tuple[Callable,list,dict[str,Any]]|list]|tuple[Callable,list[Any],dict[str,Any]]|None=None, start_position:int=0, start_enabled:bool=True, actions_length:int|None=None, actions_insertion_type:int=0) -> None:
        if actions is None: actions = []
        self.actions_insertion_type = actions_insertion_type
        start_position = self.get_index(start_position)
        self.current_position = start_position
        self.set_actions(actions, actions_length)
        self.progress = Animation.Animation(self.current_position / (self.actions_length - 1), None, TRANSITION_TIME, Bezier.ease_out)
        self.length = length
        self.is_vertical = is_vertical
        self.currently_clicking = False
        self.mouse_pos = (0, 0)
        self.position = position
        self.switch_time = 0.0
        self.surface = self.get_new_surface(time.time())
        super().__init__(self.surface, position, start_enabled=start_enabled)

    def set_actions(self, actions:list[tuple[Callable,list,dict[str,Any]]|list]|tuple[Callable,list[Any],dict[str,Any]], length:int|None=None) -> None:
        '''Sets the actions of the slider. If `actions` is a single tuple, it will create a list of functions
        with length `length` that call the current slider position along with the args and kwargs.'''
        if isinstance(actions, tuple):
            func = actions[0]
            args = actions[1] if len(actions) >= 2 else []
            kwargs = actions[2] if len(actions) >= 3 else {}
            self.actions = [[(lambda: func([self.current_position, self][self.actions_insertion_type], *args, **kwargs),)]] * length
            self.actions_length = length
        else:
            self.actions = [[action] if isinstance(action, tuple) else action for action in actions]
            self.actions_length = len(self.actions)
        if self.actions_length < 2: self.disabled_because_no_actions = True
        else: self.disabled_because_no_actions = False

    def get_bounding_box(self) -> tuple[int,int,int,int]:
        '''Returns left, upper, right, and lower'''
        point1 = self.position
        if self.is_vertical:
            point2 = (self.position[0] + WIDTH, self.position[1] + self.length)
        else:
            point2 = (self.position[0] + self.length, self.position[1] + WIDTH)
        return point1[0], point1[1], point2[0], point2[1]

    def display(self) -> pygame.Surface:
        current_time = time.time()
        if current_time - self.switch_time <= TRANSITION_TIME:
            self.surface = self.get_new_surface(current_time)
        return self.surface

    def get_new_surface(self, current_time:float) -> pygame.Surface:
        
        if self.is_vertical: surface_size = (WIDTH, self.length)
        else: surface_size = (self.length, WIDTH)
        surface = pygame.Surface(surface_size, pygame.SRCALPHA)
        padding = (WIDTH - INNER_RADIUS) / 2
        slider_rect = pygame.Rect(padding, padding, surface_size[0] - padding * 2, surface_size[1] - padding * 2)
        inner_color = Colors.get("slider.inner")
        switch_color = Colors.get("slider.switch")
        border_color = Colors.get("slider.border")
        pygame.draw.rect(surface, inner_color, slider_rect, border_radius=INNER_RADIUS)
        pygame.draw.rect(surface, border_color, slider_rect, INNER_BORDER_RADIUS, border_radius=INNER_RADIUS)
        if not self.disabled_because_no_actions:
            current_position = padding + (self.length - padding * 2) * self.progress.get(current_time)
            if self.is_vertical: switch_pos = (WIDTH / 2, current_position)
            else: switch_pos = (current_position, WIDTH / 2)
            pygame.draw.circle(surface, switch_color, switch_pos, OUTER_RADIUS)
            pygame.draw.circle(surface, border_color, switch_pos, OUTER_RADIUS, OUTER_BORDER_RADIUS)
        return surface

    def get_index(self, position:int) -> int:
        '''Turns negative indexes into len - index'''
        if position < 0:
            return self.actions_length + position
        else: return position

    def set(self, new_position:int) -> None:
        new_position = self.get_index(new_position)
        self.current_position = new_position
        if not self.disabled_because_no_actions:
            self.progress.set(self.current_position / (self.actions_length - 1))
            self.switch_time = time.time()
        else: self.surface = self.get_new_surface(time.time())

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[int,int]) -> list[tuple[Drawable.Drawable]]|None:

        def mouse_down() -> None:
            if event.__dict__["button"] not in VALID_MOUSE_BUTTONS: return
            mouse_x, mouse_y = event.__dict__["pos"]
            self.mouse_pos = (mouse_x, mouse_y)
            left, top, right, bottom = self.get_bounding_box()
            if mouse_x >= left and mouse_x < right and mouse_y >= top and mouse_y < bottom:
                self.currently_clicking = True
    
        def mouse_up() -> None:
            if event.__dict__["button"] not in VALID_MOUSE_BUTTONS: return
            self.currently_clicking = False

        def mouse_motion() -> None:
            if not self.currently_clicking: return
            self.mouse_pos = event.__dict__["pos"]

        for event in events:
            match event.type:
                case pygame.MOUSEBUTTONDOWN: mouse_down()
                case pygame.MOUSEBUTTONUP: mouse_up()
                case pygame.MOUSEMOTION: mouse_motion()
        
        return_thing = None
        if self.currently_clicking and not self.disabled_because_no_actions:
            previous_position = self.current_position
            padding = (WIDTH - INNER_RADIUS) / 2
            if self.is_vertical: mouse_progress = (self.mouse_pos[1] - self.position[1] - padding) / (self.length - padding * 2)
            else:                mouse_progress = (self.mouse_pos[0] - self.position[0] - padding) / (self.length - padding * 2)
            self.current_position = max(0, min(round(mouse_progress * (self.actions_length - 1)), self.actions_length - 1))
            if self.current_position != previous_position:
                self.call(self.actions[self.current_position])
                self.set(self.current_position)
        if return_thing is not None:
            return return_thing
