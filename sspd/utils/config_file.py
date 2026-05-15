from abc import ABC, abstractmethod
import configparser
import json
import os
from typing import Any, TypeVar, overload


class Config(ABC):
    _T = TypeVar('_T')

    @overload
    @classmethod
    def ask_value(cls, prompt: str, required_type: None = None) -> str:
        ...

    @overload
    @classmethod
    def ask_value(cls, prompt: str, required_type: type[_T]) -> _T:
        ...

    @classmethod
    def ask_value(cls, prompt: str, required_type: type[_T] | None = str) -> Any:
        if required_type is None:
            required_type = str
        while True:
            try:
                return required_type(input(prompt))
            except ValueError:
                print(f" >>> Value should be '{required_type}'")

    @abstractmethod
    def _get_or_raise_key_error(self, section: str, option: str) -> Any:
        return NotImplemented

    @abstractmethod
    def set(self, section: str, option: str, value: _T) -> _T:
        return NotImplemented

    @overload
    def get(
        self, section: str, option: str, required_type: None = None, prompt_to_ask_value_if_not_exists: str = None,
    ) -> str:
        ...

    @overload
    def get(
        self, section: str, option: str, required_type: type[_T], prompt_to_ask_value_if_not_exists: str = None,
    ) -> _T:
        ...

    def get(
        self, section: str, option: str, required_type: type[_T] | None = str,
        prompt_to_ask_value_if_not_exists: str = None,
    ) -> Any:
        if required_type is None:
            required_type = str
        try:
            value = self._get_or_raise_key_error(section=section, option=option)
            return required_type(value)
        except (KeyError, TypeError):
            prompt = prompt_to_ask_value_if_not_exists or f"{section}<{option}>: "
            value = self.ask_value(prompt=prompt, required_type=required_type)
            return self.set(section=section, option=option, value=value)

    @overload
    def get_optional(
        self, section: str, option: str, default_value: None = None, set_default_value_if_not_exists: bool = True,
    ) -> Any | None:
        ...

    @overload
    def get_optional(
        self, section: str, option: str, default_value: _T, set_default_value_if_not_exists: bool = True,
    ) -> _T:
        ...

    def get_optional(
        self, section: str, option: str, default_value: _T | None = None, set_default_value_if_not_exists: bool = True,
    ) -> Any:
        try:
            return self._get_or_raise_key_error(section=section, option=option)
        except KeyError:
            if default_value is not None and set_default_value_if_not_exists:
                default_value = self.set(section=section, option=option, value=default_value)
            return default_value


class ConfigFile(Config):
    def __init__(self, config_filepath: str):
        self.__CONFIG = configparser.ConfigParser()
        if os.path.exists(path=config_filepath):
            self.__CONFIG.read(config_filepath)
        self.__CONFIG_FILEPATH = config_filepath

    @property
    def filepath(self) -> str:
        return self.__CONFIG_FILEPATH

    def _get_or_raise_key_error(self, section: str, option: str) -> Any:
        try:
            return self.__CONFIG.get(section=section, option=option).strip()
        except (configparser.NoSectionError, configparser.NoOptionError):
            raise KeyError(f"{section}<{option}> not exists")

    def set(self, section: str, option: str, value: Config._T) -> Config._T:
        sections = self.__CONFIG.sections()
        if section not in sections:
            self.__CONFIG.add_section(section)
        self.__CONFIG.set(section, option, value)
        with open(file=self.__CONFIG_FILEPATH, mode="w", encoding="UTF-8") as cf:
            self.__CONFIG.write(cf)
        return value

    def is_exists(self, section: str, option: str) -> bool:
        return self.__CONFIG.has_option(section, option)


class ConfigJSON(Config):
    def __init__(self, json_filepath: str):
        self.__CONFIG = dict()
        if os.path.exists(path=json_filepath):
            with open(json_filepath, "r", encoding="UTF-8") as jf:
                self.__CONFIG = dict(json.load(jf))
        self.__CONFIG_FILEPATH = json_filepath

    @property
    def filepath(self) -> str:
        return self.__CONFIG_FILEPATH

    def _get_or_raise_key_error(self, section: str, option: str) -> Any:
        if section not in self.__CONFIG or option not in self.__CONFIG[section]:
            raise KeyError(f"{section}<{option}> not exists")
        return self.__CONFIG[section][option]

    def set(self, section: str, option: str, value: Config._T) -> Config._T:
        if section not in self.__CONFIG:
            self.__CONFIG[section] = dict()
        self.__CONFIG[section][option] = value
        with open(self.__CONFIG_FILEPATH, "w", encoding="UTF-8") as jf:
            json.dump(self.__CONFIG, jf, ensure_ascii=False)
        return value

    def is_exists(self, section: str, option: str) -> bool:
        return section in self.__CONFIG and option in self.__CONFIG[section]
