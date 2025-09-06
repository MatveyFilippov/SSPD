from . import io
from .paths import FilePath
import os
import sys
from typing import Iterator


class IgnKeyChars:
    comment_line_startswith = "#"
    folder_endswith = "/"
    filepath_startswith = "/"


DESCRIPTION_SSPD_IGN = f"""{IgnKeyChars.comment_line_startswith} List files and folders to ignore during SSH/SCP project delivery
{IgnKeyChars.comment_line_startswith} The system will only work with files in the local project folder specified in config
{IgnKeyChars.comment_line_startswith} Always use forward slashes '/' for paths regardless of OS
{IgnKeyChars.comment_line_startswith} Supported patterns:
{IgnKeyChars.comment_line_startswith} - Lines starting with '{IgnKeyChars.comment_line_startswith}' are comments and will be ignored
{IgnKeyChars.comment_line_startswith} - Lines ending with '{IgnKeyChars.folder_endswith}' indicate folders - all files within will be ignored
{IgnKeyChars.comment_line_startswith} - Lines starting with '{IgnKeyChars.filepath_startswith}' represent absolute file or folder paths to ignore
{IgnKeyChars.comment_line_startswith} - Other lines are treated as keywords - any filepath containing the keyword (when split by '/' or '\\') will be ignored"""

DEFAULT_SSPD_IGN_CONTENT = f"""{IgnKeyChars.comment_line_startswith} For example:
{IgnKeyChars.filepath_startswith}SSPDFiles{IgnKeyChars.folder_endswith}
.git{IgnKeyChars.folder_endswith}
.gitignore
{IgnKeyChars.filepath_startswith}venv{IgnKeyChars.folder_endswith}
{IgnKeyChars.filepath_startswith}.idea{IgnKeyChars.folder_endswith}
__pycache__{IgnKeyChars.folder_endswith}
.DS_Store
{IgnKeyChars.filepath_startswith}README.md
"""


def init_default_ignore_file(filepath: str):
    with open(filepath, "w", encoding="UTF-8") as file:
        file.write(DESCRIPTION_SSPD_IGN)
    io.print_info(f"File '{os.path.join('...', os.path.sep + filepath)}' is clean. Do you want to ignore any files?")
    if not io.input_bool(
        "ENTER (to break process and fill ign file) / '{sign2continue}' (to continue without ignoring): ",
        sign2continue="No",
    ):
        return
    with open(filepath, "a+", encoding="UTF-8") as file:
        file.write("\n\n" + DEFAULT_SSPD_IGN_CONTENT)
    sys.exit(0)


class IgnoreFile:
    def __init__(self, ignore_filepath: str, project_path: str):
        ignore_filepath = ignore_filepath.strip()
        if not ignore_filepath.endswith(".ign"):
            ignore_filepath += ".ign"
        if not os.path.exists(ignore_filepath):
            init_default_ignore_file(ignore_filepath)
        self._IGNORE_FILEPATH = ignore_filepath

        project_path = project_path.strip()
        if not project_path.endswith(os.path.sep):
            project_path += os.path.sep
        if not (os.path.exists(project_path) and os.path.isdir(project_path)):
            raise FileNotFoundError(f"Can't find project dir '{project_path}'")
        self._PROJECT_DIR_PATH = project_path

        self.__files2ignore: set[FilePath] = set()
        self.__markers: set[str] = set()

    def __iter_ign_file_lines(self, skip_comment_lines=True) -> Iterator[str]:
        with open(self._IGNORE_FILEPATH, "r") as file:
            for line in file:
                line = line.strip()
                if skip_comment_lines and line.startswith(IgnKeyChars.comment_line_startswith):
                    continue
                if line == "":
                    continue
                yield line

    def __new_filepath(self, filepath: str):
        self.__files2ignore.add(FilePath.from_filepath(filepath=filepath, project_folderpath=self._PROJECT_DIR_PATH))

    def __new_folderpath(self, folderpath: str):
        while folderpath.startswith("/"):
            folderpath = folderpath.removeprefix("/")
        if not folderpath.startswith(self._PROJECT_DIR_PATH):
            folderpath = self._PROJECT_DIR_PATH + folderpath
        for root, dirs, files in os.walk(folderpath):
            for file in files:
                self.__new_filepath(os.path.join(root, file))

    def __update_split_paths_using_markers(self):
        for root, dirs, files in os.walk(self._PROJECT_DIR_PATH):
            for file in files:
                filepath = os.path.join(root, file)
                for marker in self.__markers:
                    if marker in filepath:
                        self.__new_filepath(filepath)

    def update_files2ignore(self):
        self.__files2ignore = set()
        self.__markers = set()

        for line in self.__iter_ign_file_lines():
            if line.startswith(IgnKeyChars.filepath_startswith):
                if line.endswith(IgnKeyChars.folder_endswith):
                    self.__new_folderpath(line)
                else:
                    self.__new_filepath(line)
            else:
                while line.strip().endswith("/"):
                    line = line.removesuffix("/")
                self.__markers.add(line)

        self.__update_split_paths_using_markers()

    @property
    def files2ignore(self) -> set[FilePath]:
        if not self.__files2ignore:
            self.update_files2ignore()
        return self.__files2ignore.copy()
