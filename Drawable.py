import math

import pygame


class Drawable():
    def __init__(self, surface:pygame.Surface, position:tuple[int,int]=(0,0), restore_objects:list[tuple["Drawable",int]]|None=None) -> None:
        self.surface = surface
        self.position = position
        self.should_destroy = False
        self.restore_objects = [] if restore_objects is None else restore_objects
    
    def display(self) -> pygame.Surface:
        return self.surface

    def rotate_vector(self, vector:tuple[int,int], angle:float) -> tuple[int,int]:
        x = vector[0] * math.cos(angle) - vector[1] * math.sin(angle)
        y = vector[0] * math.sin(angle) + vector[1] * math.cos(angle)
        return x, y

    def tick(self, events:list[pygame.event.Event], screen_position:tuple[int,int]) -> list[tuple["Drawable"]]|None:
        '''Used for non-display events and adding additional elements to the objects list. If the integer is -1, it will prepend, and if it's 1, it will append.'''
        pass

    def restore(self) -> None:
        self.should_destroy = False

    def destroy(self) -> list[tuple["Drawable",int]]:
        '''Used to add additional elements to the objects list when an element is destroyed.
        It will also return `restore_objects`.
        If the integer is -1, it will prepend, and if it's 1, it will append.'''
        for restore_object in self.restore_objects:
            restore_object[0].restore()
        return_stuff = self.restore_objects
        self.restore_objects = []
        return return_stuff

    # https://stackoverflow.com/questions/15098900/how-to-set-the-pivot-point-center-of-rotation-for-pygame-transform-rotate
    def rotate_around_point(self, surface, angle:int, pivot:tuple[int,int], offset:tuple[int,int]) -> pygame.Surface:
        rotated_image = pygame.transform.rotozoom(surface, -angle, 1)
        rotated_offset = self.rotate_vector(offset, angle)
        rect = rotated_image.get_rect(center=pivot + rotated_offset)
        return rotated_image, rect
