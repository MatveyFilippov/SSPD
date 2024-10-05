import configparser
import os.path


class ConfigFile:
    def __init__(self, config_path: str):
        self.config = configparser.ConfigParser()
        if os.path.exists(path=config_path):
            self.config.read(config_path)
        else:
            with open(file=config_path, mode="w", encoding="UTF-8") as c:
                self.config.write(c)
        self.config_path = config_path

    def get_required_value(self, section: str, option: str, required_type=str):
        try:
            variable = self.config.get(section, option).strip()
            if not variable:
                raise configparser.NoOptionError(section=section, option=option)
            return required_type(variable)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            variable = None
            while variable is None:
                try:
                    variable = required_type(input(f"{option}: "))
                except ValueError:
                    print(f" >>> Value should be '{required_type}'")
                    variable = None
            self.__write_value(section, option, str(variable))
        return variable

    def get_optional_value(self, section: str, option: str) -> str | None:
        try:
            variable = self.config.get(section, option).strip()
        except (configparser.NoSectionError, configparser.NoOptionError):
            variable = None
        return variable

    def __write_value(self, section: str, option: str, value: str):
        sections = self.config.sections()
        if section not in sections:
            self.config.add_section(section)
        self.config.set(section, option, value)
        with open(file=self.config_path, mode="w", encoding="UTF-8") as c:
            self.config.write(c)
