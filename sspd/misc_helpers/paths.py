from functools import lru_cache
import re


@lru_cache
def split_filepath(filepath: str) -> list[str]:
    parts = re.split(r"(/|\\)+", filepath)
    result = []
    for part in parts:
        if not part.strip() or part.count("/") or part.count("\\"):
            continue
        result.append(part.strip())
    return result


class FilePath:
    def __init__(self, *paths_from_project_dir: str):
        if len(paths_from_project_dir) < 1:
            raise ValueError("FilePath can't be empty")
        self.__ABSTRACT_PATH = paths_from_project_dir
        self.__JOINED_ABSTRACT = "/".join(self.__ABSTRACT_PATH)
        self.__paths_set: set[str] = set()
        self.__hash = None

    @property
    def abstract(self) -> str:
        return self.__JOINED_ABSTRACT

    def __contains__(self, item):
        if not self.__paths_set:
            self.__paths_set = set(self.__ABSTRACT_PATH)
        return item in self.__paths_set

    def __iter__(self):
        return iter(self.__ABSTRACT_PATH)

    def __hash__(self):
        if self.__hash is None:
            self.__hash = hash(self.__ABSTRACT_PATH)
        return self.__hash

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, FilePath):
            return False
        return self.__ABSTRACT_PATH == other.__ABSTRACT_PATH

    def __str__(self):
        return self.__JOINED_ABSTRACT

    def __repr__(self):
        return f"FilePath(abstract='{self.__JOINED_ABSTRACT}')"

    def to_absolute(self, project_folderpath: str) -> str:
        if not project_folderpath.endswith("/"):
            project_folderpath += "/"
        return project_folderpath + self.__JOINED_ABSTRACT

    def child(self, *file_or_folder_names: str) -> 'FilePath':
        return FilePath(*(self.__ABSTRACT_PATH + file_or_folder_names))

    def parent(self) -> 'FilePath':
        if len(self.__ABSTRACT_PATH) <= 1:
            return self
        return FilePath(*(self.__ABSTRACT_PATH[:-1]))

    @classmethod
    def from_filepath(cls, filepath: str, project_folderpath: str | None = "") -> 'FilePath':
        filepath = filepath.removeprefix(project_folderpath)
        return cls(*tuple(part for part in split_filepath(filepath)))
