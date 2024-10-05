import os
import re


def split_filepath(filepath: str) -> list[str]:
    parts = re.split(r'(/|\\)+', filepath)
    result = []
    for part in parts:
        part = part.strip()
        if not part or part.count("/") or part.count("\\"):
            continue
        result.append(part.strip())
    return result


class IgnKeyChars:
    comment_line_startswith = "#"
    folder_endswith = "/"
    filepath_startswith = "/"


DESCRIPTION_SSPD_IGN = f"""{IgnKeyChars.comment_line_startswith} Put here files & folders that you want to ignore in ssh/scp project delivering process
{IgnKeyChars.comment_line_startswith} System will work with files in local project folder that you put in config
{IgnKeyChars.comment_line_startswith} Supported keys:
{IgnKeyChars.comment_line_startswith} Line starts with '{IgnKeyChars.comment_line_startswith}' is comment - system won't look them
{IgnKeyChars.comment_line_startswith} Line ends with '{IgnKeyChars.folder_endswith}' is folder - system will ignore all files in this dir
{IgnKeyChars.comment_line_startswith} Line starts with '{IgnKeyChars.filepath_startswith}' is final filepath/folderpath
{IgnKeyChars.comment_line_startswith} If line don't starts with any keys system will take it as 'marker' to ignore...
{IgnKeyChars.comment_line_startswith} ... if filepath (split by `/` or `\\`) contains 'marker' --- system will ignore it"""

DEFAULT_SSPD_IGN_CONTENT = f"""
{IgnKeyChars.comment_line_startswith} For example:
sspd{IgnKeyChars.folder_endswith}
ssh_scp_project_delivery.py
{IgnKeyChars.filepath_startswith}.git{IgnKeyChars.folder_endswith}
.gitignore
{IgnKeyChars.filepath_startswith}playground.py
venv{IgnKeyChars.folder_endswith}
.idea{IgnKeyChars.folder_endswith}
__pycache__{IgnKeyChars.folder_endswith}
.DS_Store
{IgnKeyChars.filepath_startswith}README.md
"""


def init_default_ignore_file(filepath: str):
    with open(filepath, 'w', encoding="UTF-8") as file:
        file.write(DESCRIPTION_SSPD_IGN)
    print(f"File '{os.path.join('...', os.path.sep+filepath)}' is clean. Do you want to ignore any files?")
    sign2continue = "No"
    user_decision = input(f"Enter (to break process and fill ign file) / '{sign2continue}' (to continue without ignoring): ")
    if user_decision.strip() == sign2continue:
        return
    with open(filepath, 'a+', encoding="UTF-8") as file:
        file.write(DEFAULT_SSPD_IGN_CONTENT)
    os.abort()


class IgnoreFile:
    def __init__(self, ignore_filepath: str, project_path: str):
        ignore_filepath = ignore_filepath.strip()
        if not ignore_filepath.endswith(".ign"):
            ignore_filepath += ".ign"
        if not os.path.exists(ignore_filepath):
            init_default_ignore_file(ignore_filepath)
        self.IGNORE_FILEPATH = ignore_filepath

        project_path = project_path.strip()
        if not project_path.endswith(os.path.sep):
            project_path += os.path.sep
        if not (os.path.exists(project_path) and os.path.isdir(project_path)):
            raise FileNotFoundError(f"Can't find project dir '{project_path}'")
        self.PROJECT_DIR_PATH = project_path

        self.__files2ignore = None
        self.__markers: set[str] = set()
        self.__split_paths: list[list[str]] = []

    @property
    def files2ignore(self) -> set[str]:
        if not self.__files2ignore:
            self.update_files2ignore()
        return self.__files2ignore.copy()

    def update_files2ignore(self):
        self.__files2ignore = set()
        self.__markers = set()
        self.__split_paths = []
        for line in self.__iter_ign_file_lines(skip_comment_lines=True):
            if line.startswith(IgnKeyChars.filepath_startswith):
                if line.endswith(IgnKeyChars.folder_endswith):
                    self.__new_folderpath(line)
                else:
                    self.__new_filepath(line)
            else:
                while line.endswith("/") or line.endswith("\\"):
                    line = line[:1]
                self.__markers.add(line)
        self.__update_split_paths_using_markers()
        self.__export_absolute_filepaths()

    def __iter_ign_file_lines(self, skip_comment_lines=False) -> str:
        with open(self.IGNORE_FILEPATH, "r") as file:
            for line in file.readlines():
                line = line.strip()
                if skip_comment_lines and line.startswith(IgnKeyChars.comment_line_startswith):
                    continue
                if line == "":
                    continue
                yield line

    def __update_split_paths_using_markers(self):
        for root, dirs, files in os.walk(self.PROJECT_DIR_PATH):
            for file in files:
                filepath = split_filepath(
                    os.path.join(root, file).replace(self.PROJECT_DIR_PATH, "")
                )
                for marker in self.__markers:
                    if marker in filepath:
                        self.__split_paths.append(filepath)

    def __new_filepath(self, filepath: str):
        self.__split_paths.append(split_filepath(filepath))

    def __new_folderpath(self, folderpath: str):
        for root, dirs, files in os.walk(os.path.join(self.PROJECT_DIR_PATH, folderpath)):
            for file in files:
                filepath = os.path.join(root, file).replace(self.PROJECT_DIR_PATH, "")
                self.__new_filepath(filepath)

    def __export_absolute_filepaths(self):
        for split_path in self.__split_paths:
            self.__files2ignore.add(
                os.path.join(
                    self.PROJECT_DIR_PATH,
                    os.path.sep.join(split_path)
                )
            )
