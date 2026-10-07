from abc import ABC, abstractmethod
import os
from typing import AnyStr, Iterable
import pathspec


class IgnoreManager(ABC):
    def reload(self):  # Possible to implement, but not mandatory
        pass

    @abstractmethod
    def is_path_ignored(self, _path: str) -> bool:
        return NotImplemented


class SimpleIgnoreManager(IgnoreManager):
    @staticmethod
    def _get_spec(patterns: Iterable[AnyStr]):
        return pathspec.PathSpec.from_lines('gitwildmatch', patterns)

    def __init__(self, patterns: Iterable[AnyStr]):
        self._SPEC = self._get_spec(patterns)

    def is_path_ignored(self, _path: str) -> bool:
        return self._SPEC.match_file(file=_path)


DEFAULT_IGNORE_FILE_CONTENT = """# List files and folders to ignore during SSH/SFTP project delivery
# The system will only work with files in the local project folder specified in config
# gitignore-style patterns are supported

# For example:
*.md

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
virtualenv/
pyenv/

# IDE
.idea/
.vscode/

# System
.DS_Store
*.log
.git/
.gitignore
"""


class IgnoreFile(SimpleIgnoreManager):
    @staticmethod
    def create_default_file(filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "a+", encoding="UTF-8") as file:
            file.write(DEFAULT_IGNORE_FILE_CONTENT)

    @staticmethod
    def _load_patterns(filepath: str) -> list[str]:
        with open(filepath, "r", encoding="UTF-8") as file:
            return file.readlines()

    def __init__(self, filepath: str):
        super().__init__(self._load_patterns(filepath))
        self._IGNORE_FILEPATH = filepath

    def reload(self):
        self._SPEC = self._get_spec(self._load_patterns(self._IGNORE_FILEPATH))

    @classmethod
    def create_default_file_if_not_exists(cls, filepath: str) -> 'IgnoreFile':
        if not os.path.isfile(filepath):
            cls.create_default_file(filepath)
        return cls(filepath)
