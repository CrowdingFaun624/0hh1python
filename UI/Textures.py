import os

import pygame

import Utilities.Settings as Settings

def get_textures() -> dict[str,pygame.Surface]:
    file_list = os.listdir("./_img")
    output:dict[str,pygame.Surface] = {}
    for file_name in file_list:
        output[file_name] = pygame.image.load(os.path.join("./_img", file_name))
    return output

textures = get_textures()

TEXTURES = {
    "close": ["close_dark.png", "close_light.png"],
    "cog": ["cog_dark.png", "cog_light.png"],
    "eye": ["eye_dark.png", "eye_light.png"],
    "history": ["history_dark.png", "history_light.png"],
    "lock": "lock.png",
    "logo_32": "logo_32.png",
    "logo_1024": "logo_1024.png",
}

def get(name:str) -> pygame.Surface:
    file_name = TEXTURES[name]
    if isinstance(file_name, list):
        file_name = file_name[Settings.settings["light_mode"]]
    return textures[file_name]
