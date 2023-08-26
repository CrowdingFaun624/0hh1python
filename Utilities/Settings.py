import json
import os

default = { # stores defaults
    "hard_mode": False,
    "light_mode": False,
    "axis_counters": False,
    "count_remaining": True,
    "counters_left": False,
    "counters_top": True,
}

def create_if_non_existant() -> None:
    if not os.path.exists("./settings.json"):
        with open("./settings.json", "wt") as f:
            f.write(json.dumps(default, indent=2))

def make_sure_all_keys_exist() -> None:
    changed = False
    with open("./settings.json", "rt") as f:
        try:
            data = json.loads(f.read())
        except json.decoder.JSONDecodeError:
            changed = True
            data = {}
    if not isinstance(data, dict): data = {}; changed = True
    new = {}
    for name, value in data.items():
        if name in default:
            changed = True
            new[name] = data[name]
    for name, value in default.items():
        if name not in data:
            changed = True
            new[name] = value
    if changed:
        with open("./settings.json", "wt") as f:
            f.write(json.dumps(new, indent=2))

def get_settings() -> dict[str,any]:
    with open("./settings.json", "rt") as f:
        return json.loads(f.read())

def write(name:str, value:any) -> None:
    if name not in settings: raise KeyError("Setting \"%s\" does not exist!" % name)
    settings[name] = value
    with open("./settings.json", "wt") as f:
        f.write(json.dumps(settings, indent=2))

create_if_non_existant()
make_sure_all_keys_exist()

settings = get_settings()
