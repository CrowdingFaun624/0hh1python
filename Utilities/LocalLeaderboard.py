import json

import Utilities.JsonFileManager as JsonFileManager

SCORE_DELTA_TIME = 1 / 60

default = {
    "score": 0,
    # "times_12_12_2_0": 0, # how many times board was done. Bigger length, smaller length, colors, difficulty.
    # "time_record_12_12_2_0": None, # minimum time. 
    # "time_average_12_12_2_0": None, # average time.
}

manager = JsonFileManager.JsonFileManager("local_leaderboard", default, is_strict=False)

manager.create_if_non_existant()
manager.check_all_keys_exist()

leaderboard = manager.contents

def increase_score(amount:int) -> None:
    if not isinstance(amount, int):
        raise TypeError("Can only raise score by an int!")
    manager.write("score", leaderboard["score"] + amount)

def complete_board(size:tuple[int,int], colors:int, usable_rules:list[bool], axis_counters:bool, solve_time:float) -> None:
    if not isinstance(size, tuple) or not all(isinstance(item, int) for item in size) or len(size) != 2:
        show_value = str(size) if isinstance(size, tuple) else str(type(size))
        raise TypeError("`size` must be a tuple of two integers, but is instead \"%s\"!" % show_value)
    if not isinstance(colors, int) or colors not in range(2, 37):
        show_value = str(colors) if isinstance(colors, int) else str(type(colors))
        raise TypeError("`colors` must be an integer within [2, 36], but is instead \"%s\"!" % show_value)
    if not isinstance(usable_rules, list) and all(isinstance(item, int) for item in usable_rules) and len(usable_rules) > 0:
        show_value = str(usable_rules) if isinstance(usable_rules, list) else str(type(usable_rules))
        raise TypeError("`difficulty` must be a list of integers, but is instead \"%s\"!" % show_value)
    if not isinstance(solve_time, float) or solve_time <= 0.0:
        show_value = str(solve_time) if isinstance(solve_time, float) else str(type(solve_time))
        raise TypeError("`solve_time` must be a float greater than 0.0, but is instead \"%s\"!" % show_value)
    if not isinstance(axis_counters, bool):
        raise TypeError("`axis_counters` must be a bool, but is instead \"%s\"!" % str(type(axis_counters)))
    big, small = max(size), min(size)
    board_code = "%i_%i_%i_%s_%i" % (big, small, colors, "[" + ",".join(str(int(rule)) for rule in usable_rules) + "]", int(axis_counters))
    times_key = "board_total_%s" % board_code
    record_key = "board_record_%s" % board_code
    average_key = "board_average_%s" % board_code
    times = leaderboard[times_key] if times_key in leaderboard else 0
    record = leaderboard[record_key] if record_key in leaderboard else 2147483647.0
    average = leaderboard[average_key] if average_key in leaderboard else 2147483647
    new_times = times + 1
    new_record = min(record, solve_time)
    new_average = (average * times + solve_time) / new_times
    manager.writes({times_key: new_times, record_key: new_record, average_key: new_average})
    increase_score(size[0] * size[1])
