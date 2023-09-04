import Utilities.JsonFileManager as JsonFileManager

default = { # stores defaults
    "hard_mode": False,
    "light_mode": False,
    "axis_counters": False,
    "count_remaining": True,
    "counters_left": False,
    "counters_top": True,
    "axis_checkboxes": False,
}

manager = JsonFileManager.JsonFileManager("settings", default)

manager.create_if_non_existant()
manager.check_all_keys_exist()

settings = manager.contents
