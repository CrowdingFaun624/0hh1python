from collections.abc import Callable

import pygame

import UI.Drawable as Drawable


class Button(Drawable.Drawable):
    def __init__(self, surface:pygame.Surface, position:tuple[int,int], restore_objects:list[tuple[Drawable.Drawable,int]]|None=None, children:list[Drawable.Drawable,int]|None=None, left_click_action:tuple[Callable[[],None|list[tuple[Drawable.Drawable,int]]],list[any],dict[str,any]]|list|None=None, right_click_action:tuple[Callable[[],None|list[tuple[Drawable.Drawable,int]]],list[any],dict[str,any]]|list|None=None, start_enabled:bool=True) -> None:
        if left_click_action is None: self.left_click_action = []
        elif isinstance(left_click_action, list): self.left_click_action = left_click_action
        else: self.left_click_action = [left_click_action]
        if right_click_action is None: self.right_click_action = []
        elif isinstance(right_click_action, list): self.right_click_action = right_click_action
        else: self.right_click_action = [right_click_action]
        self.enabled = start_enabled
        super().__init__(surface, position, restore_objects, children)
        self.started_clicking = self.is_clicking()
    
    def is_clicking(self, mouse_position:tuple[int,int]|None=None) -> bool:
        if mouse_position is None: mouse_position = pygame.mouse.get_pos()
        surface_size = self.surface.get_size()
        screen_position = self.position
        other_corner = (screen_position[0] + surface_size[0], screen_position[1] + surface_size[1])
        return pygame.mouse.get_pressed() and self.enabled and (mouse_position[0] >= screen_position[0] and mouse_position[0] < other_corner[0] and mouse_position[1] >= screen_position[1] and mouse_position[1] < other_corner[1])

    def call(self, functions:tuple[Callable[[],None|list[tuple[Drawable.Drawable,int]]]|list|None,list[any],dict[str,any]], return_stuff:list|None=None) -> list[tuple[Drawable.Drawable,int]]|None:
        return_things = []
        for function in functions:
            callable = function[0]
            args = function[1] if len(function) >= 2 else []
            kwargs = function[2] if len(function) >= 3 else {}
            return_thing = callable(*args, **kwargs)
            if return_thing is not None: return_things.extend(return_thing)
        if return_stuff is not None: return_stuff.extend(return_things)
        return return_things

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[int,int]) -> list[tuple[Drawable.Drawable,int]]|None:
        if self.started_clicking:
            if self.is_clicking(): return
            else: self.started_clicking = False
        return_stuff = []
        for event in events:
            match event.type:
                case pygame.MOUSEBUTTONDOWN:
                    if not self.is_clicking(event.__dict__["pos"]): continue
                    if event.__dict__["button"] == 1:
                        self.call(self.left_click_action, return_stuff)
                    elif event.__dict__["button"] == 3:
                        self.call(self.right_click_action, return_stuff)
        return return_stuff
