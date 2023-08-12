from collections.abc import Callable

import pygame

import UI.Button as Button
import UI.Drawable as Drawable
import UI.Textures as Textures

class ButtonPanel(Drawable.Drawable):
    def __init__(self, button_parameters:list[tuple[str|pygame.Surface,tuple[Callable[[],None|list[tuple[Drawable.Drawable,int]]]]]], top_constraint:int, bottom_constraint:int, left_constraint:int, right_constraint:int) -> None:
        def scale_texture(surface:pygame.Surface) -> pygame.Surface:
            multiplier = round(((vertical_space / 130) * 16) / 16)
            return pygame.transform.scale_by(surface, multiplier)
        if top_constraint > bottom_constraint: raise ValueError("Top constraint is greater than bottom restraint!")
        if left_constraint > right_constraint: raise ValueError("Left constraint is greater than right constraint!")
        vertical_space = bottom_constraint - top_constraint
        horizontal_space = right_constraint - left_constraint
        buttons = [Button.Button(scale_texture(Textures.textures[button[0]] if isinstance(button[0], str) else button[0]), (0, 0), None, left_click_action=button[1]) for button in button_parameters]
        sum_of_button_width = sum((button.surface.get_size()[0] for button in buttons))
        spacing = (horizontal_space - sum_of_button_width) / (len(buttons) + 1)
        x = left_constraint
        for button in buttons:
            y = int((top_constraint + bottom_constraint) / 2 - button.surface.get_size()[1] / 2)
            x += spacing
            button.position = (x, y)
            x += button.surface.get_size()[0]
        super().__init__(None, (0, 0), children=buttons)