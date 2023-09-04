import pygame

import UI.ButtonPanel as ButtonPanel
import UI.Colors as Colors
import UI.Drawable as Drawable
import UI.Fonts as Fonts
import UI.Menu as Menu
import UI.Tile as Tile
import Utilities.LocalLeaderboard as LocalLeaderboard

ROW_HEIGHT = 120
ROW_PADDING = 20
COLUMN_PADDING = 10
OTHER_STATS_WIDTH = 0.5
RECORDS_WIDTH = 0.5

class LeaderboardMenu(Menu.Menu):
    def get_title(self) -> str:
        return "Leaderboards"
    
    def get_scores(self) -> dict[tuple[tuple[int,int],int,int,bool],dict[str,int|float]]:
        leaderboard = LocalLeaderboard.leaderboard
        output:dict[tuple[tuple[int,int],int,int,bool],dict[str,int|float]] = {}
        for key, value in leaderboard.items():
            if not key.startswith("board_"): continue
            _, data_point, width, height, colors, difficulty, axis_counters = key.split("_")
            board_data = (int(colors), (int(width), int(height)), int(difficulty), bool(int(axis_counters)))
            if board_data not in output: output[board_data] = {}
            output[board_data][data_point] = value
        for board_data, values in output.items():
            if len(values) != 3:
                raise ValueError("Board \"%s\" does not have the correct length of 3 (currently %i)!" % (str(board_data), len(values)))
        output = dict(sorted(list(output.items())))
        return output

    def get_objects(self) -> list[Drawable.Drawable]:

        def time_from_float(seconds:float) -> str:
            hours_int = int(seconds // 3600)
            minutes_int = int((seconds // 60) % 60)
            seconds_int = int(seconds % 60)
            seconds_remainder = seconds % 1
            hours_str = str(hours_int).zfill(2)
            minutes_str = str(minutes_int).zfill(2)
            seconds_str = str(seconds_int).zfill(2)
            remainder_str = ("%.3f" % seconds_remainder)[2:]
            if hours_int > 0:     return "%s:%s:%s.%s" % (hours_str, minutes_str, seconds_str, remainder_str)
            else: return "%s:%s.%s" % (minutes_str, seconds_str, remainder_str)

        scores = self.get_scores()
        previous_color = 0
        current_value = 0
        is_even = False

        top_constraint = self.position[1] + self.display_size[1] / 7.5
        bottom_constraint = ButtonPanel.ButtonPanel.top_constraint
        left_constraint = self.position[0]
        right_constraint = self.position[0] + self.display_size[0]
        x = self.position[0]
        y = top_constraint

        menu_objects:list[Drawable.Drawable] = []

        for board_data, records in list(scores.items()):
            colors, size, difficulty, axis_counters = board_data
            if previous_color == colors:
                current_value -= 1
                current_value = ((current_value - 1) % colors) + 1
            else:
                previous_color = colors
                current_value = colors
            is_even = not is_even
            
            tile = Tile.Tile(0, ROW_HEIGHT, current_value, is_even, 2, 0.0)
            tile.position = (x, y)
            tile_size = tile.surface.get_size()
            menu_objects.append(tile)

            size_text = "%i×%i" % size
            size_surface = Fonts.get_fitted_font(size_text, "josefin", ROW_HEIGHT * 0.75, tile_size[0] * 0.8, tile_size[1] * 0.8).render(size_text, True, Colors.get("font"))
            size_surface_size = size_surface.get_size()
            size_object = Drawable.Drawable(size_surface, (x + (tile_size[0] - size_surface_size[0]) / 2, y + (tile_size[1] - size_surface_size[1]) / 2))
            menu_objects.append(size_object)

            colors_text = "Colors: %i" % colors
            difficulty_text = "Difficulty: %i" % difficulty
            axis_counters_text = "Has Axis Counters" if axis_counters else "No Axis Counters"
            other_stats_width = (self.display_size[0] - tile_size[0] - COLUMN_PADDING * 2) * OTHER_STATS_WIDTH
            other_stats_font = Fonts.get_fitted_font_multi([colors_text, difficulty_text, axis_counters_text], "josefin", int(ROW_HEIGHT / 3), other_stats_width, ROW_HEIGHT / 3)
            
            colors_surface = other_stats_font.render(colors_text, True, Colors.get("font"))
            difficulty_surface = other_stats_font.render(difficulty_text, True, Colors.get("font"))
            axis_counters_surface = other_stats_font.render(axis_counters_text, True, Colors.get("font"))

            other_stats_surfaces = [colors_surface, difficulty_surface, axis_counters_surface]
            max_width = max(surface.get_width() for surface in other_stats_surfaces)
            other_stats_surface = pygame.Surface((max_width, ROW_HEIGHT), pygame.SRCALPHA)
            other_stats_surface.blits((surface, (0, index * ROW_HEIGHT / 3)) for index, surface in enumerate(other_stats_surfaces))
            other_stats_object = Drawable.Drawable(other_stats_surface, (x + tile_size[0] + COLUMN_PADDING, y))
            menu_objects.append(other_stats_object)

            total_text = "Total: %i" % records["total"]
            record_text = "Record: %s" % time_from_float(records["record"])
            average_text = "Average: %s" % time_from_float(records["average"])
            records_width = (self.display_size[0] - tile_size[0] - COLUMN_PADDING * 2) * RECORDS_WIDTH
            records_font = Fonts.get_fitted_font_multi([total_text, record_text, average_text], "josefin", int(ROW_HEIGHT / 3), records_width, ROW_HEIGHT / 3)

            total_surface = records_font.render(total_text, True, Colors.get("font"))
            record_surface = records_font.render(record_text, True, Colors.get("font"))
            average_surface = records_font.render(average_text, True, Colors.get("font"))

            records_surfaces = [total_surface, record_surface, average_surface]
            max_width = max(surface.get_width() for surface in records_surfaces)
            records_surface = pygame.Surface((max_width, ROW_HEIGHT), pygame.SRCALPHA)
            records_surface.blits((surface, (0, index * ROW_HEIGHT / 3)) for index, surface in enumerate(records_surfaces))
            records_object = Drawable.Drawable(records_surface, (x + tile_size[0] + COLUMN_PADDING + other_stats_width, y))
            menu_objects.append(records_object)

            if y > bottom_constraint: self.scrollable = True
            y += ROW_HEIGHT + ROW_PADDING

        self.scroll_height = y - self.display_size[1] + ButtonPanel.ButtonPanel.vertical_space
        return menu_objects