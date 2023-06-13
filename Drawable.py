import math
import pygame

class Drawable():
    def __init__(self, surface:pygame.Surface) -> None:
        self.surface = surface
    
    def display(self, ticks:int) -> pygame.Surface:
        return self.surface

    def rotate_vector(self, vector:tuple[int,int], angle:float) -> tuple[int,int]:
        x = vector[0] * math.cos(angle) - vector[1] * math.sin(angle)
        y = vector[0] * math.sin(angle) + vector[1] * math.cos(angle)
        return x, y

    # https://stackoverflow.com/questions/15098900/how-to-set-the-pivot-point-center-of-rotation-for-pygame-transform-rotate
    def rotate_around_point(self, surface, angle:int, pivot:tuple[int,int], offset:tuple[int,int]) -> pygame.Surface:
        rotated_image = pygame.transform.rotozoom(surface, -angle, 1)
        rotated_offset = self.rotate_vector(offset, angle)
        rect = rotated_image.get_rect(center=pivot + rotated_offset)
        return rotated_image, rect
