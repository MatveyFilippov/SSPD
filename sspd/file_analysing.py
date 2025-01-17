import os
import hashlib
from . import base, exceptions


def get_checksum(data: str | bytes) -> str:
    if type(data) == str:
        data = data.encode()
    checksum = hashlib.md5()
    checksum.update(data)
    return checksum.hexdigest()


def is_byte_content_different(local: bytes, remote: bytes) -> bool:
    return get_checksum(local) != get_checksum(remote)


def get_filenames_in_remote_dir(folder_path: str, root_path="", *filenames2ignore: str) -> set[str]:
    try:
        result = set()
        for remote_filename in base.SFTP_REMOTE_MACHINE.listdir(folder_path):
            if remote_filename in filenames2ignore:
                continue
            remote_absolute_path = folder_path + "/" + remote_filename
            if remote_filename.count("."):
                file2add = remote_absolute_path.replace(f"{root_path}/", "")
                while file2add.startswith("/"):
                    file2add.removeprefix("/")
                result.add(file2add)
            else:
                result.update(get_filenames_in_remote_dir(
                    remote_absolute_path, root_path, *filenames2ignore
                ))
        return result
    except FileNotFoundError:
        raise exceptions.SSPDException(f"It isn't a file (not contains '.') or folder in remote project dir '{folder_path}'")


def get_filenames_in_local_dir(folder_path: str, *filenames2ignore: str) -> set[str]:
    result = set()
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file in filenames2ignore:
                continue
            local_absolute_path = os.path.join(root, file)
            file2add = local_absolute_path.replace(f"{folder_path}/", "")
            while file2add.startswith("/"):
                file2add.removeprefix("/")
            result.add(file2add)
    return result


class FileAnalysing:
    def __init__(self, local_dir: str, remote_dir: str, *filenames2ignore: str):
        self.LOCAL_DIR_PATH = local_dir
        self.REMOTE_DIR_PATH = remote_dir
        self.FILENAMES_TO_IGNORE = filenames2ignore

        self.LOCAL_FILES: set[str] = set()
        self.REMOTE_FILES: set[str] = set()
        self.__updated_files: set[str] = set()
        self.__new_files: set[str] = set()
        self.__deleted_files: set[str] = set()

        self.refresh()

    def refresh(self):
        self.LOCAL_FILES = get_filenames_in_local_dir(self.LOCAL_DIR_PATH, *self.FILENAMES_TO_IGNORE)
        self.REMOTE_FILES = get_filenames_in_remote_dir(
            self.REMOTE_DIR_PATH, self.REMOTE_DIR_PATH, *self.FILENAMES_TO_IGNORE,
        )

        self.__updated_files = set()
        self.__new_files = set()
        self.__deleted_files = set()

    @property
    def updated_files(self) -> set[str]:
        if self.__updated_files:
            return self.__updated_files.copy()
        self.__updated_files = set()
        for filename in self.REMOTE_FILES:
            if filename in self.LOCAL_FILES and self.__is_file_updated(filename):
                self.__updated_files.add(filename)
        return self.__updated_files.copy()

    def __is_file_updated(self, filename: str) -> bool:
        local_filepath = os.path.join(self.LOCAL_DIR_PATH, filename)
        remote_filepath = self.REMOTE_DIR_PATH + "/" + filename
        try:
            with open(local_filepath, "rb") as local_file:
                local_file_bytes = local_file.read()
            with base.SFTP_REMOTE_MACHINE.open(remote_filepath, "r") as remote_file:
                remote_file_bytes = remote_file.read()
            return is_byte_content_different(local_file_bytes, remote_file_bytes)
        except UnicodeDecodeError:
            return True

    @property
    def new_files(self) -> set[str]:
        if self.__new_files:
            return self.__new_files.copy()
        for filename in self.LOCAL_FILES:
            if filename not in self.REMOTE_FILES:
                self.__new_files.add(filename)
        return self.__new_files.copy()

    @property
    def deleted_files(self) -> set[str]:
        # TODO: you can look, that remote file not in local files (as in `new_files` but reversed)
        # but here is problem - remote project can create special files, so them will be always deleted
        return self.__deleted_files.copy()
