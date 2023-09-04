from collections.abc import Callable

import pygame

import UI.Button as Button
import UI.Drawable as Drawable
import UI.Enablable as Enablable
import UI.Textures as Textures


MAX_BUTTON_SIZE = 64 # buttons with textures larger than this will be shrunk

class ButtonPanel(Enablable.Enablable):
    '''Creates a horizontal row of buttons. Give it a list of button parameters. Arguments: string (texture name) or (surface and function to recreate that surface); (click function, positional arguments, keyword arguments)'''
    def scale_texture(self, surface:pygame.Surface, vertical_space:float) -> pygame.Surface:
        surface_size = surface.get_size()
        multiplier = round((((vertical_space / 90) * (64 / max(surface_size))) * 16)) / 16
        return pygame.transform.scale_by(surface, multiplier)
    def __init__(self, button_parameters:list[tuple[str|tuple[pygame.Surface,tuple[Callable[[],pygame.Surface]],list,dict],tuple[Callable[[],None|list[tuple[Drawable.Drawable,int]]],list[any],dict[any]]]]) -> None:
        self.button_texture_parameters = [button[0] for button in button_parameters]
        buttons = [Button.Button(self.scale_texture(Textures.get(button[0]) if isinstance(button[0], str) else button[0][0], ButtonPanel.vertical_space), (0, 0), None, left_click_action=button[1]) for button in button_parameters]
        self.children = buttons
        self.calculate_positions()
        super().__init__(None, (0, 0), children=buttons)
    
    position:tuple[int,int]=(0, 0)
    top_constraint = 0
    bottom_constraint = 0
    left_constraint = 0
    right_constraint = 0

    def set_position(display_size:tuple[int,int]) -> None:
        '''Called at startup; sets values to consistent values.'''
        width = display_size[0] * 0.75
        ButtonPanel.top_constraint = display_size[1] * 0.9
        ButtonPanel.bottom_constraint = display_size[1]
        ButtonPanel.vertical_space = ButtonPanel.bottom_constraint - ButtonPanel.top_constraint
        ButtonPanel.position = ((display_size[0] - width) / 2, ButtonPanel.top_constraint)
        ButtonPanel.left_constraint = ButtonPanel.position[0]
        ButtonPanel.right_constraint = ButtonPanel.position[0] + width

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
