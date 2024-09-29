import pygame

import UI.Colors as Colors
import UI.Drawable as Drawable
import UI.Enablable as Enablable

WIDTH = 10
MAX_HEIGHT = 300
MIN_HEIGHT = 30

class Scrollbar(Enablable.Enablable):

    def __init__(self, total_height:int, objects_to_scroll:list[Drawable.Drawable], current_scroll:float=0.0) -> None:
        self.total_height = total_height
        self.objects_to_scroll = objects_to_scroll
        self.current_scroll = current_scroll
        self.is_dragging = False
        super().__init__(None, (0, 0), [], [])
        self.reload()

    def get_position(self) -> None:
        horizontal_space = self.right_constraint - self.left_constraint
        self.position = (self.left_constraint + (horizontal_space - WIDTH) / 2, self.current_scroll * (self.vertical_space - self.scrollbar_height))

    @staticmethod
    def set_position(display_size:tuple[int,int]) -> None:
        '''Called at startup; sets values to consistent values.'''
        Scrollbar.left_constraint = display_size[0] - WIDTH
        Scrollbar.right_constraint = display_size[0]
        Scrollbar.vertical_space = display_size[1]

    def reload(self, current_time:float=0.0) -> None:
        self.scrollbar_height = min(MAX_HEIGHT, max(MIN_HEIGHT, int(self.vertical_space * self.vertical_space / self.total_height)))
        self.get_position()
        self.surface = pygame.Surface((WIDTH, self.scrollbar_height), pygame.SRCALPHA)
        self.surface.fill(Colors.get("scrollbar"))


    def mouse_button_down(self, event:pygame.event.Event) -> None:
        mouse_x, mouse_y = event.__dict__["pos"]
        width, height = self.surface.get_size()
        x, y = self.position
        if mouse_x > x and mouse_x <= x + width and mouse_y > y and mouse_y <= y + height:
            self.is_dragging = True

    def mouse_button_up(self, event:pygame.event.Event) -> None:
        self.is_dragging = False

    def mouse_motion(self, event:pygame.event.Event) -> None:
        if not self.is_dragging: return
        relative = event.__dict__["rel"]
        if relative[1] == 0: return
        previous_scroll = self.current_scroll * self.total_height
        new_y = self.position[1] + relative[1]
        self.current_scroll =  new_y / (self.vertical_space - self.scrollbar_height)
        self.current_scroll = min(1.0, max(0.0, self.current_scroll))
        self.get_position()
        current_scroll = self.current_scroll * self.total_height
        relative_scroll = previous_scroll - current_scroll
        for scroll_object in self.objects_to_scroll:
            scroll_object.position = (scroll_object.position[0], scroll_object.position[1] + relative_scroll)

    def mouse_wheel(self, event:pygame.event.Event) -> None:
        previous_scroll = self.current_scroll * self.total_height
        current_height = self.current_scroll * self.total_height
        current_height += -30 * event.__dict__["precise_y"]
        self.current_scroll = current_height / self.total_height
        self.current_scroll = min(1.0, max(0.0, self.current_scroll))
        self.get_position()
        current_scroll = self.current_scroll * self.total_height
        relative_scroll = previous_scroll - current_scroll
        for scroll_object in self.objects_to_scroll:
            scroll_object.position = (scroll_object.position[0], scroll_object.position[1] + relative_scroll)

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[float,float]) -> list[Drawable.Drawable]|None:

        for event in events:
            match event.type:
                case pygame.MOUSEBUTTONDOWN: self.mouse_button_down(event)
                case pygame.MOUSEBUTTONUP:   self.mouse_button_up(event)
                case pygame.MOUSEMOTION:     self.mouse_motion(event)
                case pygame.MOUSEWHEEL:      self.mouse_wheel(event)
