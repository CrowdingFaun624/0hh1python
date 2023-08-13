import pygame
from collections.abc import Callable

import UI.Button as Button
import UI.ButtonPanel as ButtonPanel
import UI.Colors as Colors
import UI.Drawable as Drawable
import UI.Fonts as Fonts
import UI.SwitchButton as SwitchButton
import Utilities.Animation as Animation
import Utilities.Bezier as Bezier
import Utilities.Settings as Settings

FADE_TIME = 0.1
BUTTON_TEXT_PADDING = 12

TOGGLEABLE=0

class SettingsMenu(Drawable.Drawable):
    def __get_settings(self) -> None:
        self.settings:list[tuple[str|tuple[str,str],any,int,list[tuple[Callable,list[any],dict[str,any]]]|None,list[tuple[Callable,list[any],dict[str,any]]]|None]] = [ # title|(off title, on title), setting name, setting type, description, off functions, on functions
            ("Hard mode", "hard_mode", TOGGLEABLE, "", None, None),
            (("Dark mode", "Light mode"), "light_mode", TOGGLEABLE, "", [(self.reload_everything,)], [(self.reload_everything,)]),
        ]

    def __init__(self, window_size:tuple[int,int], reload_carrier:list[bool], surface:pygame.Surface|None=None, restore_objects:list[tuple[Drawable.Drawable,int]]|None=None, children:list[Drawable.Drawable]|None=None) -> None:
        if children is None: children = []
        self.opacity = Animation.Animation(1.0, 0.0, FADE_TIME, Bezier.ease_in)
        self.is_closing = False
        self.window_size = window_size
        self.reload_carrier = reload_carrier
        self.display_size = (self.window_size[0] * 0.75, self.window_size[1])
        self.position = ((self.window_size[0] - self.display_size[0]) / 2, (self.window_size[1] - self.display_size[1]) / 2)
        self.__get_settings()
        additional_children = self.__get_additional_children()
        additional_children.extend(self.get_settings_objects())
        super().__init__(surface, self.position, restore_objects, children + additional_children)

    def __get_additional_children(self) -> list[Drawable.Drawable]:
        return [
            self.get_title(),
            ButtonPanel.ButtonPanel([("close", (self.button_close,))], self.position[1] + 0.9 * self.display_size[1], self.window_size[1], self.position[0], self.position[0] + self.display_size[0]),
            ]

    def change_text(self, title:Drawable.Drawable, new_text:str, font_parameters:tuple[int,int,int,pygame.Color]) -> None:
        font = Fonts.get_fitted_font(new_text, "josefin", font_parameters[0], font_parameters[1], font_parameters[2])
        title.surface = font.render(new_text, True, font_parameters[3])

    def get_settings_objects(self) -> list[Drawable.Drawable]:
        y = self.position[1] + self.display_size[1] / 7.5
        output:list[Drawable.Drawable] = []
        for title, setting_name, setting_type, description, turn_off_functions, turn_on_functions in self.settings:
            font_parameters = []
            current_value = Settings.settings[setting_name]
            text = Drawable.Drawable(None, (0, 0))
            match setting_type:
                case TOGGLEABLE:
                    if isinstance(title, str):
                        off_functions = [(Settings.write, [setting_name, False])]; on_functions = [(Settings.write, [setting_name, True])]
                        if turn_off_functions is not None: off_functions.extend(turn_off_functions)
                        if turn_on_functions is not None: on_functions.extend(turn_on_functions)
                        setter = SwitchButton.SwitchButton((0, 0), toggle_on_action=on_functions, toggle_off_action=off_functions, start_toggled=current_value)
                    elif isinstance(title, tuple):
                        off_functions = [(Settings.write, [setting_name, False]), (self.change_text, [text, title[1], font_parameters])]; on_functions = [(Settings.write, [setting_name, True]), (self.change_text, [text, title[1], font_parameters])]
                        if turn_off_functions is not None: off_functions.extend(turn_off_functions)
                        if turn_on_functions is not None: on_functions.extend(turn_on_functions)
                        setter = SwitchButton.SwitchButton((0, 0), toggle_on_action=on_functions, toggle_off_action=off_functions, start_toggled=current_value)
                        title = title[current_value]
            setter_width = setter.surface.get_size()[0]
            font_parameters.extend([50, self.display_size[0] - setter_width, 50, Colors.get("font")])
            font = Fonts.get_fitted_font(title, "josefin", font_parameters[0], font_parameters[1], font_parameters[2])
            text.surface = font.render(title, True, Colors.get("font"))
            setter.position = (self.position[0], y)
            output.append(setter)
            text.position = (self.position[0] + setter_width + BUTTON_TEXT_PADDING, y)
            output.append(text)
            y += 50
        return output

    def get_title(self) -> Drawable.Drawable:
        font = Fonts.get_fitted_font("Settings", "molle", 90, self.display_size[0], self.display_size[1] / 10)
        font_surface = font.render("Settings", True, Colors.get("font"))
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

    def reload(self, current_time:float) -> None:
        self.children = self.__get_additional_children() + self.get_settings_objects()
        return super().reload(current_time)

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[int,int]) -> list[tuple[Drawable.Drawable]]|None:
        if self.is_closing and self.opacity.get() == 0.0:
            self.should_destroy = True

    def reload_everything(self) -> None:
        self.reload_carrier[0] = True
