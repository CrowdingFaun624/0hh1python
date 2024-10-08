import math
from typing import Sequence

import pygame

import Utilities.Exceptions as Exceptions


class Drawable():
    def __init__(self, surface:pygame.Surface|None=None, position:tuple[float,float]|None=None, restore_objects:list[tuple["Drawable",int]]|None=None, children:Sequence["Drawable"]|None=None) -> None:
        self.surface = surface
        self.position:tuple[float,float] = (0, 0) if position is None else position
        self.should_destroy = False
        self.restore_objects = [] if restore_objects is None else restore_objects
        self.children = [] if children is None else children

    def get_surface(self) -> pygame.Surface:
        if self.surface is None:
            raise Exceptions.AttributeNoneError("surface", self)
        return self.surface

    def display(self) -> pygame.Surface|None:
        return self.surface

    def rotate_vector(self, vector:tuple[int,int], angle:float) -> tuple[float,float]:
        x = vector[0] * math.cos(angle) - vector[1] * math.sin(angle)
        y = vector[0] * math.sin(angle) + vector[1] * math.cos(angle)
        return x, y

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[float,float]) -> list["Drawable"]|None:
        '''Used for non-display events and adding additional elements to the objects list. If the integer is -1, it will prepend, and if it's 1, it will append.'''
        ...

    def restore(self) -> None:
        self.should_destroy = False

    def reload(self, current_time:float) -> None:
        '''Used to force everything to redraw itself due to a theme change or something.'''
        for child in self.children:
            child.reload(current_time)
        for object in self.restore_objects:
            object[0].reload(current_time)

    def destroy(self) -> list[tuple["Drawable",int]]:
        '''Used to add additional elements to the objects list when an element is destroyed.
        It will also return `restore_objects`.
        If the integer is -1, it will prepend, and if it's 1, it will append.'''
        for restore_object in self.restore_objects:
            restore_object[0].restore()
        return_stuff = self.restore_objects
        self.restore_objects = []
        return return_stuff

    def delete(self) -> None:
        '''Frees up the object's stuff and things. Is called when the program is terminated.'''
        for child in self.children:
            child.delete()
        for restore_object in self.restore_objects:
            restore_object[0].delete()

    def update(self, object:"Drawable") -> None:
        '''Sets this object to have the surface and position of the input object.
        Can be used when references to this object must be preserved.'''
        self.surface = object.surface
        self.position = object.position
        self.children = object.children
        self.restore_objects = object.restore_objects

    def set_alpha(self, value:int, this_surface:pygame.Surface|None=None) -> None:
        '''Sets the alpha of an object and its children. If an object does not have a surface attribute, use this_surface.'''
        if this_surface is not None:
            this_surface.set_alpha(value)
        elif self.surface is not None:
            self.surface.set_alpha(value)
        for child in self.children:
            child.set_alpha(value)

    # https://stackoverflow.com/questions/15098900/how-to-set-the-pivot-point-center-of-rotation-for-pygame-transform-rotate
    def rotate_around_point(self, surface, angle:int, pivot:tuple[int,int], offset:tuple[int,int]) -> tuple[pygame.Surface, pygame.Rect]:
        rotated_image = pygame.transform.rotozoom(surface, -angle, 1)
        rotated_offset = self.rotate_vector(offset, angle)
        rect = rotated_image.get_rect(center=pivot + rotated_offset)
        return rotated_image, rect
