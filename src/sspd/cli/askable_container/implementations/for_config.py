import configparser
import os
from typing import Any
from ..container import AskableContainer


class AskableConfig(AskableContainer):
    def __init__(self, config_filepath: str):
        config_file_parent_dir = os.path.dirname(config_filepath)
        if not os.path.exists(config_file_parent_dir):
            raise FileNotFoundError(f"No such directory for config file: '{config_file_parent_dir}'")

        self._data = configparser.ConfigParser()
        if os.path.isfile(path=config_filepath):
            self._data.read(config_filepath)
        self.__FILEPATH = config_filepath

    @property
    def filepath(self) -> str:
        return self.__FILEPATH

    def is_section_exists(self, section: str) -> bool:
        return self._data.has_section(section=section)

    def is_section_and_option_exists(self, section: str, option: str) -> bool:
        return self._data.has_option(section=section, option=option)

    def _get_raw_value_or_raise_key_error(self, section: str, option: str) -> Any:
        try:
            return self._data.get(section=section, option=option).strip()
        except (configparser.NoSectionError, configparser.NoOptionError):
            raise KeyError(f"{section}<{option}> not exists")

    @staticmethod
    def _value_to_str(value: Any) -> str:
        if value is None:
            return "none"
        elif isinstance(value, bool):
            return str(value).lower()
        return str(value)

    def set(self, section: str, option: str, value: AskableContainer._T) -> AskableContainer._T:
        sections = self._data.sections()
        if section not in sections:
            self._data.add_section(section)
        self._data.set(section=section, option=option, value=self._value_to_str(value))
        with open(file=self.__FILEPATH, mode="w", encoding="UTF-8") as cf:
            self._data.write(cf)
        return value

    def is_exists(self, section: str, option: str) -> bool:
        return self._data.has_option(section, option)
