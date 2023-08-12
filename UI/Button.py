from collections.abc import Callable

import pygame

import UI.Drawable as Drawable


class Button(Drawable.Drawable):
    def __init__(self, surface:pygame.Surface, position:tuple[int,int], restore_objects:list[tuple[Drawable.Drawable,int]]|None=None, children:list[Drawable.Drawable,int]|None=None, left_click_action:tuple[Callable[[],None|list[tuple[Drawable.Drawable,int]]],list[any],dict[str,any]]|None=None, right_click_action:tuple[Callable[[],None|list[tuple[Drawable.Drawable,int]]],list[any],dict[str,any]]|None=None, start_enabled:bool=True) -> None:
        if left_click_action is not None:
            self.left_click_action = left_click_action[0]
            self.left_click_args = left_click_action[1] if len(left_click_action) >= 2 else []
            self.left_click_kwargs = left_click_action[2] if len(left_click_action) >= 3 else {}
        else: self.left_click_action = None
        if right_click_action is not None:
            self.right_click_action = right_click_action[0]
            self.right_click_args = right_click_action[1] if len(right_click_action) >= 2 else []
            self.right_click_kwargs = right_click_action[2] if len(right_click_action) >= 3 else {}
        else: self.right_click_action = None
        self.enabled = start_enabled
        super().__init__(surface, position, restore_objects, children)
        self.started_clicking = self.is_clicking()
    
    def is_clicking(self, mouse_position:tuple[int,int]|None=None) -> bool:
        if mouse_position is None: mouse_position = pygame.mouse.get_pos()
        surface_size = self.surface.get_size()
        screen_position = self.position
        other_corner = (screen_position[0] + surface_size[0], screen_position[1] + surface_size[1])
        return pygame.mouse.get_pressed() and self.enabled and (mouse_position[0] >= screen_position[0] and mouse_position[0] < other_corner[0] and mouse_position[1] >= screen_position[1] and mouse_position[1] < other_corner[1])

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[int,int]) -> list[tuple[Drawable.Drawable]]|None:
        if self.started_clicking:
            if self.is_clicking(): return
            else: self.started_clicking = False
        return_stuff = []
        for event in events:
            match event.type:
                case pygame.MOUSEBUTTONDOWN:
                    if not self.is_clicking(event.__dict__["pos"]): continue
                    if event.__dict__["button"] == 1:
                        if self.left_click_action is None: continue
                        return_thing = self.left_click_action(*self.left_click_args, **self.left_click_kwargs)
                        if isinstance(return_thing, list): return_stuff.extend(return_thing)
                    elif event.__dict__["button"] == 3:
                        if self.right_click_action is None: continue
                        return_thing = self.right_click_action(*self.right_click_args, **self.right_click_kwargs)
                        if isinstance(return_thing, list): return_stuff.extend(return_thing)
        return return_stuff
