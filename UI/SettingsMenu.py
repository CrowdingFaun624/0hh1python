from collections.abc import Callable

import pygame

import UI.ButtonPanel as ButtonPanel
import UI.Colors as Colors
import UI.Drawable as Drawable
import UI.Fonts as Fonts
import UI.Menu as Menu
import UI.SwitchButton as SwitchButton
import Utilities.Settings as Settings

BUTTON_TEXT_PADDING = 12

TOGGLEABLE=0

class SettingsMenu(Menu.Menu):
    def __get_settings(self) -> None:
        self.settings:list[tuple[str|tuple[str,str],any,int,list[tuple[Callable,list[any],dict[str,any]]]|None,list[tuple[Callable,list[any],dict[str,any]]]|None]] = [
            # title|(off title, on title), setting name, setting type, description, off functions, on functions
            ("Hard Mode", "hard_mode", TOGGLEABLE, "", None, None),
            (("Dark Mode", "Light Mode"), "light_mode", TOGGLEABLE, "", [(self.reload_everything,)], [(self.reload_everything,)]),
            ("Row/Column Counters", "axis_counters", TOGGLEABLE, "Show how many tiles are of each color.", None, None),
            ("Count Remaining", "count_remaining", TOGGLEABLE, "", None, None),
            (("Counters on Right", "Counters on Left"), "counters_left", TOGGLEABLE, "", None, None),
            (("Counters on Bottom", "Counters on Top"), "counters_top", TOGGLEABLE, "", None, None),
            ("Axis Checkboxes", "axis_checkboxes", TOGGLEABLE, "", None, None),
        ]

    def __init__(self, window_size:tuple[int,int], reload_carrier:list[bool], restore_objects:list[tuple[Drawable.Drawable,int]]|None=None, children:list[Drawable.Drawable]|None=None) -> None:
        self.__get_settings()
        super().__init__(window_size, reload_carrier, restore_objects, children)

    def change_text(self, title:Drawable.Drawable, new_text:str, font_parameters:tuple[int,int,int,pygame.Color]) -> None:
        font = Fonts.get_fitted_font(new_text, "josefin", font_parameters[0], font_parameters[1], font_parameters[2])
        title.surface = font.render(new_text, True, font_parameters[3])

    def get_objects(self) -> list[Drawable.Drawable]:
        top_constraint = self.position[1] + self.display_size[1] / 7.5
        bottom_constraint = ButtonPanel.ButtonPanel.top_constraint
        y = top_constraint
        output:list[Drawable.Drawable] = []
        for title, setting_name, setting_type, description, turn_off_functions, turn_on_functions in self.settings:
            font_parameters = []
            current_value = Settings.settings[setting_name]
            text = Drawable.Drawable(None, (0, 0))
            match setting_type:
                case TOGGLEABLE:
                    if isinstance(title, str):
                        off_functions = [(Settings.manager.write, [setting_name, False])]; on_functions = [(Settings.manager.write, [setting_name, True])]
                        if turn_off_functions is not None: off_functions.extend(turn_off_functions)
                        if turn_on_functions is not None: on_functions.extend(turn_on_functions)
                        setter = SwitchButton.SwitchButton((0, 0), toggle_on_action=on_functions, toggle_off_action=off_functions, start_toggled=current_value)
                    elif isinstance(title, tuple):
                        off_functions = [(Settings.manager.write, [setting_name, False]), (self.change_text, [text, title[1], font_parameters])]; on_functions = [(Settings.manager.write, [setting_name, True]), (self.change_text, [text, title[1], font_parameters])]
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
            if y >= bottom_constraint: self.scrollable = True
            y += 50
        self.scroll_height = y - self.display_size[1] + ButtonPanel.ButtonPanel.vertical_space
        return output

    def get_title(self) -> str:
        return "Settings"
