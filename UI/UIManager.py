import pygame

import UI.Board as Board
import UI.Button as Button
import UI.ButtonPanel as ButtonPanel
import UI.Drawable as Drawable
import UI.Intro as Intro
import UI.LevelSelector as LevelSelector
import UI.LoadingScreen as LoadingScreen
import UI.SettingsMenu as SettingsMenu

reload_carrier = None # set to `[False]` by Main.py

def get_main_object() -> Drawable.Drawable:
    ButtonPanel.ButtonPanel.set_position(pygame.display.get_window_size())
    return Intro.Intro(pygame.display.get_window_size(), exit_intro)

def exit_intro(intro:Intro.Intro) -> list[tuple[Drawable.Drawable,int]]:
    return [(LevelSelector.LevelSelector(pygame.display.get_window_size(), enter_board_from_level_selector, enter_settings_from_level_selector), 1)]

def enter_board_from_level_selector(level_selector:LevelSelector.LevelSelector) -> list[tuple[Drawable.Drawable,int]]:
    for child in level_selector.children:
        if isinstance(child, Button.Button): child.enabled = False
    size, colors = level_selector.board_settings
    board_size = min(level_selector.display_size[0], level_selector.display_size[1] * 0.75, LevelSelector.MAXIMUM_BOARD_SIZE)
    corner = (int((level_selector.display_size[0] - board_size) / 2), int((level_selector.display_size[1] - board_size) / 2))
    board = Board.Board(size, colors=colors, position=corner, pixel_size=board_size, restore_objects=[(level_selector, 1)], window_size=level_selector.display_size)
    return [(LoadingScreen.LoadingScreen(board, (board_size, board_size), level_selector.display_size, finish_loading_screen, position=((level_selector.display_size[0] - board_size) / 2, (level_selector.display_size[1] - board_size) / 2)), 1)]

def finish_loading_screen(loading_screen:LoadingScreen.LoadingScreen) -> list[tuple[Drawable.Drawable,int]]|None:
    if loading_screen.closed_early: return None
    loading_screen.board.opacity.set(1.0)
    return [(loading_screen.board, -1)]

def enter_settings_from_level_selector(level_selector:LevelSelector.LevelSelector) -> list[tuple[Drawable.Drawable,int]]:
    level_selector.opacity.set(0.0)
    level_selector.enabled = False
    level_selector.is_fading_out = True
    for child in level_selector.children:
        if isinstance(child, Button.Button): child.enabled = False
    return [(SettingsMenu.SettingsMenu(level_selector.display_size, restore_objects=[(level_selector, -1)], reload_carrier=reload_carrier), 1)]
