import pygame

import Drawable

class Button(Drawable.Drawable):
    def __init__(self, surface:pygame.Surface, left_click_action:tuple[any,list[any],dict[str,any]]=None, right_click_action:tuple[any,list[any],dict[str,any]]=None) -> None:
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
        super().__init__(surface)
