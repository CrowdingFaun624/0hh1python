import pygame

import Utilities.Settings as Settings

COLORS = { # lists of colors are [dark mode, light mode]
    "background": [pygame.Color(34, 34, 34), pygame.Color(222, 222, 222)],
    "font": [pygame.Color(255, 255, 255), pygame.Color(0, 0, 0)],
    "font.tile": pygame.Color(255, 255, 255),
    "font.loading_screen_progress": pygame.Color(128, 128, 128),

    "loading_bar.border": [pygame.Color(255, 255, 255), pygame.Color(0, 0, 0)],
    "loading_bar.incomplete": [pygame.Color(16, 16, 16), pygame.Color(64, 64, 64)], # complete color is the tile color.

    "switch_button.inner_off": pygame.Color(16, 16, 16),
    "switch_button.inner_on": pygame.Color(216, 216, 216),
    "switch_button.outer": [pygame.Color(240, 240, 240), pygame.Color(20, 20, 20)],
    "switch_button.border": [pygame.Color(255, 255, 255), pygame.Color(0, 0, 0)],
    "switch_button.switch": pygame.Color(128, 128, 128),

    "tile.0": [pygame.Color(42, 42, 42), pygame.Color(213, 213, 213)],
    "tile.1_even": pygame.Color(213, 83, 54),
    "tile.1_odd": pygame.Color(194, 75, 49),
    "tile.2_even": pygame.Color(53, 184, 213),
    "tile.2_odd": pygame.Color(48, 167, 194),
    "tile.3_even": pygame.Color(213, 184, 53),
    "tile.3_odd": pygame.Color(194, 167, 48),
    "tile.4_even": pygame.Color(83, 213, 54),
    "tile.4_odd": pygame.Color(75, 194, 49),
    "tile.shadow": pygame.Color(0, 0, 0, 51),
    "tile.highlight": [pygame.Color(255, 255, 255), pygame.Color(0, 0, 0)]
}
def get(name:str) -> pygame.Color:
    color = COLORS[name]
    if isinstance(color, list):
        return color[Settings.settings["light_mode"]]
    else: return color

def get_non_conflicting_colors(colors:list[pygame.Color]) -> pygame.Color:
    '''Returns a color that is not in the list.'''
    rs = [color.r for color in colors]
    gs = [color.g for color in colors]
    bs = [color.b for color in colors]
    r, g, b = 0, 0, 0
    while r in rs:
        r += 1
    if r > 255: raise ValueError("Failed to find red value!")
    while g in gs:
        g += 1
    if g > 255: raise ValueError("Failed to find green value!")
    while b in bs:
        b += 1
    if b > 255: raise ValueError("Failed to find blue value!")
    return pygame.Color(r, g, b)

def is_exist(name:str) -> bool:
    return name in COLORS
