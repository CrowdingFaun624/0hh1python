from collections.abc import Callable

import pygame

import UI.Button as Button
import UI.Drawable as Drawable
import UI.Textures as Textures

class ButtonPanel(Drawable.Drawable):
    '''Creates a horizontal row of buttons. Give it a list of button parameters. Arguments: string (texture name) or (surface and function to recreate that surface); (click function, positional arguments, keyword arguments)'''
    def scale_texture(self, surface:pygame.Surface, vertical_space:float) -> pygame.Surface:
        multiplier = round(((vertical_space / 130) * 16) / 16)
        return pygame.transform.scale_by(surface, multiplier)
    def __init__(self, button_parameters:list[tuple[str|tuple[pygame.Surface,tuple[Callable[[],pygame.Surface]],list,dict],tuple[Callable[[],None|list[tuple[Drawable.Drawable,int]]]]]], top_constraint:int, bottom_constraint:int, left_constraint:int, right_constraint:int) -> None:
        if top_constraint > bottom_constraint: raise ValueError("Top constraint is greater than bottom restraint!")
        if left_constraint > right_constraint: raise ValueError("Left constraint is greater than right constraint!")
        vertical_space = bottom_constraint - top_constraint
        self.top_constraint = top_constraint; self.bottom_constraint = bottom_constraint; self.right_constraint = right_constraint; self.left_constraint = left_constraint
        self.button_texture_parameters = [button[0] for button in button_parameters]
        buttons = [Button.Button(self.scale_texture(Textures.get(button[0]) if isinstance(button[0], str) else button[0][0], vertical_space), (0, 0), None, left_click_action=button[1]) for button in button_parameters]
        self.children = buttons
        self.calculate_positions()
        super().__init__(None, (0, 0), children=buttons)
    
    def disable(self) -> None:
        for button in self.children:
            button.enabled = False
    
    def enable(self) -> None:
        for button in self.children:
            button.enabled = True

    def calculate_positions(self) -> None:
        horizontal_space = self.right_constraint - self.left_constraint
        sum_of_button_width = sum((button.surface.get_size()[0] for button in self.children))
        spacing = (horizontal_space - sum_of_button_width) / (len(self.children) + 1)
        x = self.left_constraint
        for button in self.children:
            y = int((self.top_constraint + self.bottom_constraint) / 2 - button.surface.get_size()[1] / 2)
            x += spacing
            button.position = (x, y)
            x += button.surface.get_size()[0]

    def reload(self, current_time:float) -> None:
        for texture_parameter, button in zip(self.button_texture_parameters, self.children):
            if isinstance(texture_parameter, str):
                button.surface = self.scale_texture(Textures.get(texture_parameter), self.bottom_constraint - self.top_constraint)
            else:
                function = texture_parameter[1][0]
                args = texture_parameter[1][1] if len(texture_parameter[1]) >= 2 else []
                kwargs = texture_parameter[1][1] if len(texture_parameter[1]) >= 3 else {}
                button.surface = self.scale_texture(function(*args, **kwargs), self.bottom_constraint - self.top_constraint)
        self.calculate_positions()
        return super().reload(current_time)
