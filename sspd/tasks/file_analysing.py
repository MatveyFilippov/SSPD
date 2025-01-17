import os
import hashlib
from sspd import base, exceptions


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
    FILENAMES_TO_IGNORE = base.IGNORE.files2ignore

    LOCAL_FILES: set[str] = set()
    REMOTE_FILES: set[str] = set()

    __updated_files: set[str] = set()
    __new_files: set[str] = set()
    __deleted_files: set[str] = set()

    @classmethod
    def refresh(cls):
        cls.LOCAL_FILES = get_filenames_in_local_dir(base.LOCAL_PROJECT_DIR_PATH, *cls.FILENAMES_TO_IGNORE)
        cls.REMOTE_FILES = get_filenames_in_remote_dir(
            base.REMOTE_PROJECT_DIR_PATH, base.REMOTE_PROJECT_DIR_PATH, *cls.FILENAMES_TO_IGNORE,
        )

        cls.__updated_files = set()
        cls.__new_files = set()
        cls.__deleted_files = set()

    @classmethod
    def get_updated_files(cls) -> set[str]:
        if cls.__updated_files:
            return cls.__updated_files.copy()
        cls.__updated_files = set()
        for filename in cls.REMOTE_FILES:
            if filename in cls.LOCAL_FILES and cls.__is_file_updated(filename):
                cls.__updated_files.add(filename)
        return cls.__updated_files.copy()

    @classmethod
    def __is_file_updated(cls, filename: str) -> bool:
        local_filepath = os.path.join(base.LOCAL_PROJECT_DIR_PATH, filename)
        remote_filepath = base.REMOTE_PROJECT_DIR_PATH + "/" + filename
        try:
            with open(local_filepath, "rb") as local_file:
                local_file_bytes = local_file.read()
            with base.SFTP_REMOTE_MACHINE.open(remote_filepath, "r") as remote_file:
                remote_file_bytes = remote_file.read()
            return is_byte_content_different(local_file_bytes, remote_file_bytes)
        except UnicodeDecodeError:
            return True

    @classmethod
    def get_new_files(cls) -> set[str]:
        if cls.__new_files:
            return cls.__new_files.copy()
        for filename in cls.LOCAL_FILES:
            if filename not in cls.REMOTE_FILES:
                cls.__new_files.add(filename)
        return cls.__new_files.copy()

    @classmethod
    def get_deleted_files(cls) -> set[str]:
        # TODO: you can look, that remote file not in local files (as in `new_files` but reversed)
        # but here is problem - remote project can create special files, so them will be always deleted
        return cls.__deleted_files.copy()
