import json
import os
from typing import Any


class JsonFileManager():
    def __init__(self, file_name:str, default:dict, is_strict:bool=True) -> None:
        assert "/" not in file_name
        assert "." not in file_name
        self.file_name = file_name
        self.file_path = "./%s.json" % self.file_name
        self.default = default
        self.is_strict = is_strict # if it errors if you try to write to a key that doesn't exist.
        self.contents = self.get_values()

    def create_if_non_existant(self) -> None:
        if not os.path.exists(self.file_path):
            with open(self.file_path, "wt") as f:
                json.dump(self.default, f, indent=2)

    def check_all_keys_exist(self) -> None:
        changed = False
        with open(self.file_path, "rt") as f:
            try:
                data = json.load(f)
            except json.decoder.JSONDecodeError:
                changed = True
                data = {}
        if not isinstance(data, dict): data = {}; changed = True
        new = {}
        if self.is_strict:
            for name, value in data.items():
                if name not in self.default:
                    changed = True
                    new[name] = data[name]
        for name, value in self.default.items():
            if name not in data:
                changed = True
                new[name] = value
        if changed:
            with open(self.file_path, "wt") as f:
                json.dump(new, f, indent=2)

    def get_values(self) -> dict[str,Any]:
        try:
            with open(self.file_path, "rt") as f:
                return json.load(f)
        except json.JSONDecodeError:
            self.check_all_keys_exist()
            with open(self.file_path, "rt") as f:
                return json.load(f)

    def write(self, name:str, value:Any) -> None:
        if name not in self.contents:
            if self.is_strict: raise KeyError("Key \"%s\" does not exist in %s!" % (name, self.file_name))
            else:
                if not isinstance(name, str): raise TypeError("`name` must be a string, but is instead \"%s\"!" % str(type(name)))
        self.contents[name] = value
        with open(self.file_path, "wt") as f:
            json.dump(self.contents, f, indent=2)

    def writes(self, data:dict[str,Any]) -> None:
        for name, value in list(data.items()):
            if name not in self.contents:
                if self.is_strict: raise KeyError("Key \"%s\" does not exist in %s!" % (name, self.file_name))
                else: pass
            self.contents[name] = value
        with open(self.file_path, "wt") as f:
            json.dump(self.contents, f, indent=2)
