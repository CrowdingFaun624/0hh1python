import time
from typing import Any, Callable

import pygame

import LevelCreator.LevelUtilities as LU
import UI.ButtonPanel as ButtonPanel
import UI.Colors as Colors
import UI.Drawable as Drawable
import UI.Enablable as Enablable
import UI.FakeBoard as FakeBoard
import UI.Fonts as Fonts
import UI.Slider as Slider
import UI.SwitchButton as SwitchButton
import UI.Textures as Textures
import Utilities.Animation as Animation
import Utilities.Bezier as Bezier
import Utilities.LocalLeaderboard as LocalLeaderboard

LEVELS = {2: (4, 20), 3: (3, 15), 4: (4, 12)}
RULES_DEFAULT = [1, 1, 1, 10, 1]

SWITCH = 0
SLIDER = 1
RULES = [ # (type, additional_settings, name)
    # Switch settings: None, Slider settings: [special case, actions length, show slider label]
    (SWITCH, None, "Three-in-a-Row"),
    (SWITCH, None, "Balancing"),
    (SWITCH, None, "Cloning"),
    (SLIDER, ("rule4", None, True), "Rule 4"),
    (SWITCH, None, "Multicolor Balancing"),
]

SECTION_PADDING_SIZE = 0.125
MAX_PER_ROW = 3
FADE_TIME = 0.1
MAXIMUM_BOARD_SIZE = 640

class LevelSelector(Enablable.Enablable):
    def __init__(self, display_size:tuple[int,int], exit_function:Callable[["LevelSelector"],list[tuple[Drawable.Drawable,int]]], screen_functions:list[Callable[["LevelSelector"],list[tuple[Drawable.Drawable,int]]]], position:tuple[int,int], restore_objects:list[tuple[Drawable.Drawable,int]]|None=None) -> None:
        self.display_size = display_size
        self.exit_function = exit_function
        self.settings_function, self.leaderboards_function = screen_functions
        self.board_settings = None
        self.is_fading_out = False
        self.has_returned_level = False
        self.enabled = True
        self.opacity = Animation.Animation(1.0, 0.0, FADE_TIME, Bezier.ease_in)
        self.level_start_opacity = Animation.Animation(0.0, None, FADE_TIME, Bezier.ease_in)
        self.surface = None # self.get_surface()
        self.mousing_over_board = False
        self.board_rules = RULES_DEFAULT
        self.lock_preview_ratio = True

        self.preview_horizontal_size = 4
        self.preview_vertical_size = 4
        self.preview_colors = 2

        self.score_text = LocalLeaderboard.leaderboard["score"]
        self.is_increasing_score = False

        self.position = position
        assert position is not None
        assert isinstance(position, tuple)
        assert len(position) == 2
        assert all(isinstance(item, int) for item in position)
        assert all(item >= 0 for item in position)
        super().__init__(self.surface, position, restore_objects, self.get_additional_children())

    def get_additional_children(self) -> list[Drawable.Drawable]:
        children = []

        children.append(ButtonPanel.ButtonPanel([("cog", (self.settings_function,[self])), ("leaderboards", (self.leaderboards_function,[self]))]))
        children.extend(self.get_score_objects())

        children.append(self.get_board_object())
        self.board_size_texts = self.get_board_text_object()
        children.extend(self.board_size_texts)
        children.extend(self.get_size_sliders())
        children.append(self.get_colors_slider())
        children.extend(self.get_rules_toggles())
        children.append(self.get_lock_object())

        return children

    def get_board_positioning_constraints(self) -> tuple[float,float,float,float]:
        '''Returns top, bottom, left, and right'''
        top_constraint = self.position[1] + self.display_size[1] * 0.1
        bottom_constraint = self.position[1] + self.display_size[1] * 0.5
        left_constraint = self.position[0] + self.display_size[0] * 0.125
        right_constraint = self.position[0] + self.display_size[0] * 0.875
        return top_constraint, bottom_constraint, left_constraint, right_constraint

    def get_board_positioning(self) -> tuple[tuple[float,float],tuple[int,int]]:
        '''Returns the preview board's position and size'''
        top_constraint, bottom_constraint, left_constraint, right_constraint = self.get_board_positioning_constraints()
        board_display_size = (right_constraint - left_constraint, bottom_constraint - top_constraint)
        size = (self.preview_horizontal_size, self.preview_vertical_size)
        maximum_tile_width = int(board_display_size[0] / size[0])
        maximum_tile_height = int(board_display_size[1] / size[1])
        tile_size = min(maximum_tile_width, maximum_tile_height)
        board_size = (size[0] * tile_size, size[1] * tile_size)
        board_position = (left_constraint + (board_display_size[0] - board_size[0]) / 2, top_constraint + (board_display_size[1] - board_size[1]) / 2)
        return (board_position, board_size)

    def get_rules_toggles(self) -> list[Drawable.Drawable]:
        def set_rule(value:Any, rule:int) -> None:
            self.board_rules[rule] = value
            # print("Set rule %i to %s" % (rule, str(value)))
        def set_rule_from(index:int, take_list:list[Any], rule:int, display_label:Drawable.Drawable|None=None, display_font:pygame.font.Font|None=None) -> None:
            self.board_rules[rule] = take_list[index]
            # print("Set rule %i to %s" % (rule, take_list[index]))
            if display_label is not None:
                surface = display_font.render(str(take_list[index]), True, Colors.get("font"))
                display_label.surface = surface
        def reload_rule4(rule_index:int, slider:Slider.Slider) -> None:
            take_list = [0] + list(range(2, (int(max(self.preview_horizontal_size, self.preview_vertical_size) // self.preview_colors) + 1)))
            special_label = self.rule_objects_special_labels[rule_index]
            slider.set_actions((set_rule_from, [take_list, rule_index, special_label[0], special_label[1]]), len(take_list))
            slider.set(0)
            set_rule_from(0, [0], rule_index, special_label[0], special_label[1])
        board_top, board_bottom, board_left, board_right = self.get_board_positioning_constraints()
        y = board_bottom + Slider.WIDTH
        x = board_left
        max_allowed_width = (board_right - board_left) / 3
        max_width_in_column = 0
        rule_changer_objects:list[Drawable.Drawable] = []
        labels:list[Drawable.Drawable] = []
        special_labels:list[tuple[Drawable.Drawable,pygame.font.Font]] = []
        special_reload_functions:list[Callable] = []
        label_font = Fonts.get_font("josefin", 30)
        font_color = Colors.get("font")
        for rule_index, rule in enumerate(RULES):
            rule_type, rule_settings, rule_name = rule
            special_reload_function = None
            special_label = None
            if rule_type is SWITCH: # I would use a match case but it doesn't work.
                rule_changer_object = SwitchButton.SwitchButton((x, y), (set_rule, [True, rule_index]), (set_rule, [False, rule_index]), self.board_rules[rule_index])
            elif rule_type is SLIDER:
                match rule_settings[0]:
                    case "rule4":
                        special_reload_function = reload_rule4
                        take_list = [0] + list(range(2, (int(max(self.preview_horizontal_size, self.preview_vertical_size) // self.preview_colors) + 1)))
                        if rule_settings[2]: # if the rule has a special label.
                            special_label = Drawable.Drawable(label_font.render(str(take_list[0]), True, font_color), (0, 0))
                            actions = (set_rule_from, [take_list, rule_index, special_label, label_font])
                        else: actions = (set_rule_from, [take_list, rule_index])
                        slider_actions_length = len(take_list)
                    case _:
                        actions = rule_settings[0]
                        try: slider_actions_length = len(rule_settings[0])
                        except AttributeError: slider_actions_length = rule_settings[1]
                rule_changer_object = Slider.Slider((x, y), max_allowed_width, False, actions, actions_length=slider_actions_length)
            special_reload_functions.append(special_reload_function)
            rule_changer_objects.append(rule_changer_object)
            if rule_changer_object.surface is None: obj_width, obj_height = rule_changer_object.get_size()
            else: obj_width, obj_height = rule_changer_object.surface.get_size()
            if special_label is not None:
                special_label.position = (x + obj_width, y)
                obj_width += special_label.surface.get_width() + 10
                special_labels.append((special_label, label_font))
                labels.append(special_label)
            else: special_labels.append(None)
            max_width_in_column = max(obj_width, max_width_in_column)
            label_object = Drawable.Drawable(label_font.render(rule_name, True, font_color), (x + obj_width, y))
            labels.append(label_object)
            y += obj_height
            if y > ButtonPanel.ButtonPanel.top_constraint - 50:
                y = board_bottom + Slider.WIDTH
                x += max_width_in_column
                max_width_in_column = 0
            
        self.rule_objects = rule_changer_objects
        self.rule_object_reload_functions = special_reload_functions
        self.rule_objects_special_labels = special_labels
        return rule_changer_objects + labels

    def get_board_object(self) -> FakeBoard.FakeBoard:
        board_position, board_size = self.get_board_positioning()
        self.display_board = FakeBoard.FakeBoard((self.preview_horizontal_size, self.preview_vertical_size), self.preview_colors, None, board_position, board_size)
        self.display_board.contents = self.display_board.get_empty_contents(self.preview_colors)
        self.display_board.reload(0.0)
        return self.display_board

    def get_lock_object_surface(self, locked:bool) -> tuple[pygame.Surface,tuple[int,int]]:
        '''Returns the surface and position of the lock object.'''
        name = {True: "locked", False: "unlocked"}[locked]
        lock_texture = Textures.get(name)
        board_top, board_bottom, board_left, board_right = self.get_board_positioning_constraints()
        top_constraint = board_top - Slider.WIDTH
        bottom_constraint = board_top
        left_constraint = board_left - Slider.WIDTH
        right_constraint = board_left
        space_width = right_constraint - left_constraint
        space_height = bottom_constraint - top_constraint
        horizontal_ratio = (space_width * 0.9) / lock_texture.get_width()
        vertical_ratio = (space_height * 0.9) / lock_texture.get_height()
        scale_ratio = max(horizontal_ratio, vertical_ratio)
        lock_surface = pygame.transform.scale_by(lock_texture, scale_ratio)
        position = (left_constraint + (space_width - lock_surface.get_width()) / 2, top_constraint + (space_height - lock_surface.get_height()) / 2)
        self.lock_object_constraints = (top_constraint, bottom_constraint, left_constraint, right_constraint)
        return lock_surface, position

    def get_lock_object(self) -> Drawable.Drawable:
        lock_surface, position = self.get_lock_object_surface(self.lock_preview_ratio)
        self.lock_object = Drawable.Drawable(lock_surface, position)
        return self.lock_object

    def get_board_text_object(self) -> tuple[Drawable.Drawable,Drawable.Drawable]:
        board_position, board_size = self.get_board_positioning()
        text = "%i×%i" % (self.preview_horizontal_size, self.preview_vertical_size)
        font = Fonts.get_fitted_font(text, "josefin", 120, board_size[0], board_size[1])
        surface = font.render(text, True, Colors.get("font"))
        surface_size = surface.get_size()
        text_position = (board_position[0] + (board_size[0] - surface_size[0]) / 2, board_position[1] + (board_size[1] - surface_size[1]) / 2)
        object1 = Drawable.Drawable(surface, text_position)

        text = "GO"
        font = Fonts.get_fitted_font(text, "josefin", 120, board_size[0], board_size[1])
        surface = font.render(text, True, Colors.get("font"))
        surface_size = surface.get_size()
        text_position = (board_position[0] + (board_size[0] - surface_size[0]) / 2, board_position[1] + (board_size[1] - surface_size[1]) / 2)
        object2 = Drawable.Drawable(surface, text_position)
        object2.set_alpha(255)

        return object1, object2

    def reload_rule_sliders(self) -> None:
        for rule_index, rule_object, rule_function in zip(range(len(self.rule_objects)), self.rule_objects, self.rule_object_reload_functions):
            if rule_function is not None:
                rule_function(rule_index, rule_object)

    def get_size_slider_functions(self) -> tuple[tuple[Callable,list[Any],dict[str,Any]],tuple[Callable,list[Any],dict[str,Any]],int]:
        def adjust_size(index:int, is_vertical:bool) -> None:
            size = size_list[index]
            if is_vertical: self.preview_vertical_size = size
            else: self.preview_horizontal_size = size
            if self.lock_preview_ratio:
                if is_vertical:
                    self.preview_horizontal_size = size
                    self.width_slider.set(self.height_slider.current_position)
                else:
                    self.preview_vertical_size = size
                    self.height_slider.set(self.width_slider.current_position)
            self.display_board.size = (self.preview_horizontal_size, self.preview_vertical_size)
            new_position, new_size = self.get_board_positioning()
            self.display_board.display_size = new_size
            self.display_board.contents = self.display_board.get_empty_contents(self.display_board.colors)
            self.display_board.set_position(new_position)
            self.display_board.reload(0.0)
            [old_object.update(new_object) for old_object, new_object in zip(self.board_size_texts, self.get_board_text_object())]
            self.reload_rule_sliders()
        colors = self.display_board.colors
        minimum, maximum = LEVELS[colors][0], LEVELS[colors][1]
        size_list = list(range(minimum, maximum + 1, colors))
        horizontal_function = (adjust_size, [False])
        vertical_function = (adjust_size, [True])
        slider_length = len(size_list)
        return horizontal_function, vertical_function, slider_length

    def get_color_slider_functions(self) -> tuple[tuple[Callable,list,dict[str,Any]],int]:
        def adjust_color(index:int) -> None:
            new_color = colors_list[index]
            self.preview_horizontal_size, self.preview_vertical_size = LEVELS[new_color][0], LEVELS[new_color][0]
            self.preview_colors = new_color
            self.display_board.size = (self.preview_horizontal_size, self.preview_vertical_size)
            new_position, new_size = self.get_board_positioning()
            self.display_board.display_size = new_size
            self.display_board.colors = new_color
            self.display_board.contents = self.display_board.get_empty_contents(new_color)
            self.display_board.set_position(new_position)
            self.display_board.reload(0.0)
            width_functions, height_functions, slider_actions_length = self.get_size_slider_functions()
            self.width_slider.set_actions(width_functions, slider_actions_length)
            self.height_slider.set_actions(height_functions, slider_actions_length)
            self.width_slider.set(0)
            self.height_slider.set(0)
            [old_object.update(new_object) for old_object, new_object in zip(self.board_size_texts, self.get_board_text_object())]
            self.reload_rule_sliders()
        colors_list = list(LEVELS.keys())
        color_function = (adjust_color,)
        slider_length = len(colors_list)
        # functions = [(adjust_color, [color]) for color in LEVELS]
        return color_function, slider_length

    def get_size_sliders(self) -> tuple[Slider.Slider,Slider.Slider]:
        horizontal_functions, vertical_functions, slider_actions_length = self.get_size_slider_functions()
        board_top, board_bottom, board_left, board_right = self.get_board_positioning_constraints()
        self.width_slider = Slider.Slider((board_left, board_top - Slider.WIDTH), board_right - board_left, False, horizontal_functions, actions_length=slider_actions_length)
        self.height_slider = Slider.Slider((board_left- Slider.WIDTH, board_top), board_bottom - board_top, True, vertical_functions, actions_length=slider_actions_length)
        return (self.width_slider, self.height_slider)

    def get_colors_slider(self) -> Slider.Slider:
        functions, slider_actions_length = self.get_color_slider_functions()
        board_top, board_bottom, board_left, board_right = self.get_board_positioning_constraints()
        horizontal_space = board_right - board_left
        slider_length = (horizontal_space) * 0.5
        self.colors_slider = Slider.Slider((board_left + (horizontal_space - slider_length) / 2, board_bottom), slider_length, False, functions, actions_length=slider_actions_length)
        return self.colors_slider

    def get_score_objects(self) -> tuple[Drawable.Drawable,Drawable.Drawable]:
        top_constraint = self.display_size[1] * 0.8
        bottom_constraint = self.display_size[1] * 0.9
        vertical_space = bottom_constraint - top_constraint
        self.score_font = Fonts.get_fitted_font(str(self.score_text), "josefin", 50, self.display_size[0] * 0.5, vertical_space)
        score_surface1 = self.score_font.render("Score ", True, Colors.get("font"))
        score_surface2 = self.score_font.render(str(self.score_text), True, Colors.get("font"))
        score1_size = score_surface1.get_size()
        score_objects = (
            Drawable.Drawable(score_surface1, (self.display_size[0] * 0.5 - score1_size[0], top_constraint + (vertical_space - score1_size[1]) / 2)),
            Drawable.Drawable(score_surface2, (self.display_size[0] * 0.5, top_constraint + (vertical_space - score1_size[1]) / 2)),
            )
        self.score_objects = score_objects
        return score_objects

    # def calculate_sizes(self) -> None:
    #     '''Calculates variables used for sizing stuff. Call this function if the window size changes.'''
    #     rows:list[list[tuple[int,int]]|None] = [] # list-type items are rows of (color, size); None are separators
    #     for color, levels in LEVELS.items():
    #         row:list[tuple[int,int]] = []
    #         for level in levels:
    #             row.append((color, level))
    #             if len(row) == MAX_PER_ROW:
    #                 rows.append(row)
    #                 row = []
    #         if len(row) > 0: rows.append(row)
    #         rows.append(None)
    #     rows.pop() # remove trailing None

    #     self.total_colors = len(LEVELS)
    #     self.max_row_length = max((len(levels) for levels in rows if levels is not None))

    #     top_constraint = self.display_size[1] * 0.125
    #     bottom_constraint = self.display_size[1] * 0.8
    #     vertical_space = bottom_constraint - top_constraint
    #     left_constraint = self.display_size[0] * 0.15
    #     right_constraint = self.display_size[0] * 0.85
    #     horizontal_space = right_constraint - left_constraint

    #     self.tile_size = min(0.142 * min(self.display_size), int(horizontal_space / self.max_row_length), int(vertical_space / (len(rows) - rows.count(None) + SECTION_PADDING_SIZE * rows.count(None))))
    #     self.section_padding_size = int(self.tile_size * SECTION_PADDING_SIZE)
    #     self.max_width = self.tile_size * self.max_row_length
    #     self.total_height = self.tile_size * (len(rows) - rows.count(None)) + (rows.count(None)) * self.section_padding_size
    #     self.position = (left_constraint + (horizontal_space - self.max_width) / 2, top_constraint + (vertical_space - self.total_height) / 2)

    #     color_patterns:dict[int,list[int]] = dict((color, [((color - i) % color) + 1 for i in range(len(LEVELS[color]), 0, -1)] if len(LEVELS[color]) > color else list(range(color, 0, -1))[:len(LEVELS[color])]) for color in LEVELS)
    #     self.tiles_positions:list[tuple[tuple[int,int,int,int,int],tuple[int,int]]] = [] # [(color, size), (x_position, y_position), ...]
    #     x_position, y_position = 0, 0 # pixels
    #     x, y = 0, 0 # tiles
    #     index = 0
    #     for row in rows:
    #         if row is None: y_position += self.section_padding_size; y = 0; index = 0; continue
    #         x_position = 0
    #         x = 0
    #         for tile in row:
    #             color, level = tile
    #             display_color = color_patterns[color][index]
    #             tile_data = (color, level, display_color, x, y)
    #             self.tiles_positions.append((tile_data, (x_position, y_position)))
    #             x += 1
    #             x_position += self.tile_size
    #             index += 1
    #         y_position += self.tile_size
    #         y += 1

    # def get_surface(self) -> pygame.Surface:
    #     self.calculate_sizes()
    #     font = Fonts.get_font("josefin", int(self.tile_size / 2))
    #     surface = pygame.Surface((self.max_width, self.total_height), pygame.SRCALPHA)
    #     current_time = time.time()
    #     for tile, position in self.tiles_positions:
    #         color, level, display_color, x, y = tile; x_position, y_position = position
    #         is_even = is_even = (x + y) % 2 == 1
    #         tile_object = Tile.Tile(0, self.tile_size, display_color, is_even, 2, current_time, mode="static")
    #         surface.blit(tile_object.surface, (x_position, y_position))
    #         font_surface = font.render(str(level), True, Colors.get("font.tile"))
    #         font_size = font_surface.get_size()
    #         font_x, font_y = (self.tile_size / 2 - font_size[0] / 2, self.tile_size / 2 - font_size[1] / 2)
    #         surface.blit(font_surface, (x_position + font_x, y_position + font_y)) # TODO: font vertical positioning is messed up.
    #     return surface

    def display(self) -> pygame.Surface:
        this_opacity = self.opacity.get()
        self.set_alpha(255 * this_opacity)
        board_size_text_opacity = self.level_start_opacity.get()
        self.board_size_texts[0].set_alpha(255 * (1.0 - board_size_text_opacity) * this_opacity)
        self.board_size_texts[1].set_alpha(255 * board_size_text_opacity * this_opacity)
        return self.surface

    def check_for_score_change(self) -> None:
        real_score = LocalLeaderboard.leaderboard["score"]
        if real_score > self.score_text:
            self.is_increasing_score = True

    def restore(self) -> None:
        self.should_destroy = False
        self.board_settings = None
        self.is_fading_out = False
        self.enable()
        self.has_returned_level = False
        self.opacity.set(1.0)
        self.check_for_score_change()
        self.test_for_mouse_over_board()

    def reload(self, current_time:float) -> None:
        # self.surface = self.get_surface()
        self.children = self.get_additional_children()
        return super().reload(current_time)

    def fade_out(self) -> None:
        self.opacity.set(0.0)
        self.is_fading_out = True
        self.disable()

    def test_for_mouse_over_board(self, mouse_position:tuple[int,int]|None=None) -> bool:
        if mouse_position is None: mouse_position = pygame.mouse.get_pos()
        if not self.enabled: return False
        mouse_x, mouse_y = mouse_position
        board_size = self.display_board.get_size()[1]
        left, top = self.display_board.position
        right, bottom = (left + board_size[0], top + board_size[1])
        is_over_board = mouse_x >= left and mouse_x < right and mouse_y >= top and mouse_y < bottom
        if self.mousing_over_board == is_over_board: return
        if is_over_board:
            self.mousing_over_board = True
            self.level_start_opacity.set(1.0)
        else:
            self.mousing_over_board = False
            self.level_start_opacity.set(0.0)
        return is_over_board

    def tick(self, events:list[pygame.event.Event], screen_position:list[int,int]) -> list[tuple[Drawable.Drawable,int]]|None:
        # def get_relative_mouse_position(position:tuple[float,float]|None=None) -> tuple[float,float]:
        #     if position is None: position = event.__dict__["pos"]
        #     return position[0] - screen_position[0], position[1] - screen_position[1]
        # def mouse_button_down() -> None:
        #     mouse_position = get_relative_mouse_position()
        #     if not self.enabled: return
        #     for tile, position, in self.tiles_positions:
        #         color, level, _, _, _ = tile
        #         x_position, y_position = position
        #         if mouse_position[0] > x_position and mouse_position[0] <= x_position + self.tile_size and mouse_position[1] > y_position and mouse_position[1] <= y_position + self.tile_size:
        #             self.board_settings = (level, color)
        #             self.fade_out()
        def mouse_button_down() -> None:
            if not self.enabled: return
            if self.mousing_over_board:
                color = self.preview_colors
                size = (self.preview_horizontal_size, self.preview_vertical_size)
                rules = self.board_rules
                self.board_settings = (size, color, rules)
                self.fade_out()
            mouse_x, mouse_y = event.__dict__["pos"]
            lock_top, lock_bottom, lock_left, lock_right = self.lock_object_constraints
            if mouse_x >= lock_left and mouse_x < lock_right and mouse_y >= lock_top and mouse_y < lock_bottom:
                self.lock_preview_ratio = not self.lock_preview_ratio
                lock_surface, lock_position = self.get_lock_object_surface(self.lock_preview_ratio)
                self.lock_object.surface = lock_surface
                self.lock_object.position = lock_position
        def mouse_motion() -> None:
            self.test_for_mouse_over_board(event.__dict__["pos"])

        current_time = time.time()

        for event in events:
            match event.type:
                case pygame.MOUSEBUTTONDOWN: mouse_button_down()
                case pygame.MOUSEMOTION: mouse_motion()
        
        if self.is_increasing_score:
            self.score_text += 1
            self.score_objects[1].surface = self.score_font.render(str(self.score_text), True, Colors.get("font"))
            if self.score_text >= LocalLeaderboard.leaderboard["score"]: self.is_increasing_score = False


        if self.is_fading_out and self.opacity.get(current_time) == 0.0: self.should_destroy = True
        if self.is_fading_out and not self.has_returned_level and self.board_settings is not None:
            self.has_returned_level = True
            return self.exit_function(self)
