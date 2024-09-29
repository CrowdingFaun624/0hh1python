import pygame

import UI.ButtonPanel as ButtonPanel
import UI.Colors as Colors
import UI.Drawable as Drawable
import UI.Enablable as Enablable
import UI.Fonts as Fonts
import UI.Scrollbar as Scrollbar
import Utilities.Animation as Animation
import Utilities.Bezier as Bezier

FADE_TIME = 0.1

class Menu(Enablable.Enablable):
    def __init__(self, window_size:tuple[int,int], reload_carrier:list[bool], restore_objects:list[tuple[Drawable.Drawable,int]]|None=None, children:list[Drawable.Drawable]|None=None) -> None:
        self.enabled = True
        if children is None: children = []
        self.opacity = Animation.Animation(1.0, 0.0, FADE_TIME, Bezier.ease_in)
        self.is_closing = False
        self.window_size = window_size
        self.reload_carrier = reload_carrier
        self.display_size = (self.window_size[0] * 0.75, self.window_size[1])
        self.position = ((self.window_size[0] - self.display_size[0]) / 2, (self.window_size[1] - self.display_size[1]) / 2)
        self.scrollable = False
        self.scroll_height = window_size[1]
        self.menu_objects = self.get_objects()
        self.scrollable_objects = self.menu_objects[:]
        additional_children = self.__get_additional_children()
        additional_children.extend(self.menu_objects)
        super().__init__(None, self.position, restore_objects, children + additional_children)

    def get_objects(self) -> list[Drawable.Drawable]:
        '''The custom list of objects to use for the menu.'''
        return []

    def __get_additional_children(self) -> list[Drawable.Drawable]:
        children:list[Drawable.Drawable] = []
        title_object = self.get_title_object()
        self.scrollable_objects.append(title_object)
        children.append(title_object)
        children.append(ButtonPanel.ButtonPanel([("close", (self.button_close,))]))
        if self.scrollable: children.append(self.get_scrollbar_object())
        return children

    def get_title(self) -> str:
        '''Returns the menu of this menu. Override this in subclasses'''
        return "Menu"

    def get_scrollbar_object(self) -> Drawable.Drawable:
        return Scrollbar.Scrollbar(self.scroll_height, self.scrollable_objects)

    def get_title_object(self) -> Drawable.Drawable:
        title = self.get_title()
        font = Fonts.get_fitted_font(title, "molle", 90, self.display_size[0], self.display_size[1] / 10)
        font_surface = font.render(title, True, Colors.get("font"))
        font_size = font_surface.get_size()
        position = (self.position[0] + (self.display_size[0] - font_size[0]) / 2, self.position[1] + (self.display_size[1] / 10 - font_size[1]) / 2)
        return Drawable.Drawable(font_surface, position)

    def button_close(self) -> None:
        self.opacity.set(0.0)
        self.is_closing = True
        self.disable()

    def display(self) -> pygame.Surface|None:
        self.set_alpha(int(255 * self.opacity.get()))
        return super().display()

    def restore(self) -> None:
        self.opacity.set(1.0)
        self.is_closing = False
        self.enable()
        super().restore()

    def reload(self, current_time:float) -> None:
        self.children = self.__get_additional_children() + self.get_objects()
        return super().reload(current_time)

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[float,float]) -> list[Drawable.Drawable]|None:
        if self.is_closing and self.opacity.get() == 0.0:
            self.should_destroy = True

    def reload_everything(self) -> None:
        self.reload_carrier[0] = True
