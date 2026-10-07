from abc import ABC, abstractmethod
import getpass
from typing import Any, TypeVar, overload
import warnings
import click


warnings.filterwarnings("ignore", category=getpass.GetPassWarning)


class AskableContainer(ABC):
    _T = TypeVar('_T')

    @abstractmethod
    def is_section_exists(self, section: str) -> bool:
        return NotImplemented

    @abstractmethod
    def is_section_and_option_exists(self, section: str, option: str) -> bool:
        return NotImplemented

    @abstractmethod
    def _get_raw_value_or_raise_key_error(self, section: str, option: str) -> Any:
        return NotImplemented

    @abstractmethod
    def set(self, section: str, option: str, value: _T) -> _T:
        return NotImplemented

    @overload
    def get(
        self, section: str, option: str,
        *, value_type: None = None, is_secret: bool = False, prompt: str = None, choices: tuple[_T, ...] = None,
    ) -> str:
        ...

    @overload
    def get(
        self, section: str, option: str,
        *, value_type: type[_T], is_secret: bool = False, prompt: str = None, choices: tuple[_T, ...] = None,
    ) -> _T:
        ...

    def get(
        self, section: str, option: str,
        *, value_type: type[_T] | None = str, is_secret: bool = False, prompt: str = None, choices: tuple[_T, ...] = None,
    ) -> Any:
        if value_type is None:
            value_type = str
        try:
            value = self._get_raw_value_or_raise_key_error(section=section, option=option)
            return value_type(value)
        except (KeyError, TypeError):
            prompt_text = prompt or f"{section}<{option}>"
            click_type = click.Choice(choices=choices) if choices else None
            value = click.prompt(text=prompt_text, hide_input=is_secret, type=click_type, value_proc=value_type)
            return self.set(section=section, option=option, value=value)

    @overload
    def get_optional(
        self, section: str, option: str,
        *, value_type:  type[_T] = Any, default_value: None = None, set_default_value_if_not_exists: bool = True,
    ) -> Any:
        ...

    @overload
    def get_optional(
        self, section: str, option: str,
        *, value_type:  type[_T] = Any, default_value: _T, set_default_value_if_not_exists: bool = True,
    ) -> _T:
        ...

    def get_optional(
        self, section: str, option: str,
        *, value_type: type[_T] = Any, default_value: _T | None = None, set_default_value_if_not_exists: bool = True,
    ) -> Any:
        try:
            value = self._get_raw_value_or_raise_key_error(section=section, option=option)
            if value_type is not Any:
                return value_type(value)
            return value
        except (KeyError, TypeError):
            if set_default_value_if_not_exists:
                default_value = self.set(section=section, option=option, value=default_value)
            return default_value
