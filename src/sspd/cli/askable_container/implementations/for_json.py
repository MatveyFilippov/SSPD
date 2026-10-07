import json
import os
from typing import Any
from ..container import AskableContainer


class AskableJSON(AskableContainer):
    def __init__(self, json_filepath: str):
        json_file_parent_dir = os.path.dirname(json_filepath)
        if not os.path.exists(json_file_parent_dir):
            raise FileNotFoundError(f"No such directory for json file: '{json_file_parent_dir}'")

        self._data = dict()
        if os.path.isfile(path=json_filepath):
            with open(json_filepath, "r", encoding="UTF-8") as jf:
                self._data = dict(json.load(jf))
        self.__FILEPATH = json_filepath

    @property
    def filepath(self) -> str:
        return self.__FILEPATH

    def is_section_exists(self, section: str) -> bool:
        return section in self._data

    def is_section_and_option_exists(self, section: str, option: str) -> bool:
        return section in self._data and option in self._data[section]

    def _get_raw_value_or_raise_key_error(self, section: str, option: str) -> Any:
        if section not in self._data or option not in self._data[section]:
            raise KeyError(f"{section}<{option}> not exists")
        return self._data[section][option]

    def set(self, section: str, option: str, value: AskableContainer._T) -> AskableContainer._T:
        if section not in self._data:
            self._data[section] = dict()
        self._data[section][option] = value
        with open(self.__FILEPATH, "w", encoding="UTF-8") as jf:
            json.dump(self._data, jf, ensure_ascii=False)
        return value

    def is_exists(self, section: str, option: str) -> bool:
        return section in self._data and option in self._data[section]
