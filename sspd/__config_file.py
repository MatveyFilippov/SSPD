import configparser
import os.path


class ConfigFile:
    def __init__(self, config_path: str):
        config_path = config_path.strip()
        self.CONFIG = configparser.ConfigParser()
        if os.path.exists(path=config_path):
            self.CONFIG.read(config_path)
        else:
            with open(file=config_path, mode="w", encoding="UTF-8") as c:
                self.CONFIG.write(c)
        self.CONFIG_PATH = config_path

    def get_required_value(self, section: str, option: str, required_type=str):
        value = self.get_optional_value(section=section, option=option, required_type=required_type)
        if value is None:
            value = self.__ask_value(prompt=f"{option}: ", required_type=required_type)
            self.__write_value_to_config(section, option, str(value))
        return value

    def get_optional_value(self, section: str, option: str, required_type=str):
        try:
            value = self.CONFIG.get(section, option).strip()
            if not value:
                raise configparser.NoOptionError(section=section, option=option)
            return required_type(value)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return None

    def __ask_value(self, prompt: str, required_type=str):
        while True:
            try:
                return required_type(input(prompt))
            except ValueError:
                print(f" >>> Value should be '{required_type}'")

    def __write_value_to_config(self, section: str, option: str, value: str):
        sections = self.CONFIG.sections()
        if section not in sections:
            self.CONFIG.add_section(section)
        self.CONFIG.set(section, option, value)
        with open(file=self.CONFIG_PATH, mode="w", encoding="UTF-8") as c:
            self.CONFIG.write(c)
