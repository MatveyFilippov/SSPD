from . import io
from .paths import FilePath
import os
import sys
import pathspec


DEFAULT_SSPD_IGN_CONTENT = """# List files and folders to ignore during SSH/SCP project delivery
# The system will only work with files in the local project folder specified in config
# gitignore-style patterns are supported

# For example:
/SSPDFiles/
.git/
.gitignore
/venv/
/.venv/
/.idea/
__pycache__/
.DS_Store
/README.md
"""


def init_default_ignore_file(filepath: str) -> bool:
    io.print_info(f"File '{os.path.join('...', os.path.sep + filepath)}' doesn't exist. Do you want to ignore any files?")
    if io.input_bool(
        "ENTER (to break process and fill ign file) / '{sign2continue}' (to continue without ignoring): ",
        sign2continue="No",
    ):
        return False
    with open(filepath, "a+", encoding="UTF-8") as file:
        file.write(DEFAULT_SSPD_IGN_CONTENT)
    sys.exit(0)


class IgnoreFile:
    @staticmethod
    def _load_ignore_spec(ignore_file: str) -> pathspec.PathSpec:
        with open(ignore_file, "r", encoding="UTF-8") as file:
            return pathspec.PathSpec.from_lines('gitwildmatch', file)

    def __init__(self, ignore_filepath: str, project_path: str):
        if not project_path.endswith(os.path.sep):
            project_path += os.path.sep
        if not (os.path.exists(project_path) and os.path.isdir(project_path)):
            raise FileNotFoundError(f"Can't find project dir '{project_path}'")
        self._PROJECT_DIR_PATH = project_path

        is_file_exists = os.path.exists(ignore_filepath)
        if not is_file_exists:
            is_file_exists = init_default_ignore_file(ignore_filepath)
        self._IGNORE_FILEPATH = ignore_filepath

        self.__SPEC = (
            self._load_ignore_spec(self._IGNORE_FILEPATH)
            if is_file_exists else
            pathspec.PathSpec(patterns=[])
        )

    def update_ignore_patterns(self):
        self.__SPEC = (
            self._load_ignore_spec(self._IGNORE_FILEPATH)
            if os.path.exists(self._IGNORE_FILEPATH) else
            pathspec.PathSpec(patterns=[])
        )

    def is_path_ignored(self, filepath: FilePath) -> bool:
        return self.__SPEC.match_file(file=filepath.abstract)
