import os

import pygame


def get_textures() -> dict[str,pygame.Surface]:
    file_list = os.listdir("./_img")
    output:dict[str,pygame.Surface] = {}
    for file_name in file_list:
        output[file_name] = pygame.image.load(os.path.join("./_img", file_name))
    return output

textures = get_textures()
