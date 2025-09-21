from .. import base, checker, exceptions
from ..misc_helpers.paths import FilePath
from functools import lru_cache
import hashlib
import os


@lru_cache(maxsize=1_000)
def get_checksum(data: str | bytes) -> str:
    if type(data) == str:
        data = data.encode()
    checksum = hashlib.md5()
    checksum.update(data)
    return checksum.hexdigest()


def is_byte_content_different(local: bytes, remote: bytes) -> bool:
    return get_checksum(local) != get_checksum(remote)


class FileAnalysing:
    LOCAL_FILES: set[FilePath] = set()
    REMOTE_FILES: set[FilePath] = set()

    __updated_files: set[FilePath] = set()
    __new_files: set[FilePath] = set()
    __deleted_files: set[FilePath] = set()

    @classmethod
    def reset_local_files(cls):
        cls.LOCAL_FILES = set(
            FilePath.from_filepath(filepath=os.path.join(root, file), project_folderpath=base.LOCAL_PROJECT_DIR_PATH)
            for root, dirs, files in os.walk(base.LOCAL_PROJECT_DIR_PATH) for file in files
        )
        cls.LOCAL_FILES.difference_update(base.IGNORE.files2ignore)

    @classmethod
    def reset_remote_files(cls):
        def get_filenames_in_remote_dir(root: str) -> set[FilePath]:
            result = set()
            try:
                for file in base.SFTP_REMOTE_MACHINE.listdir(root):
                    if root == base.REMOTE_PROJECT_DIR_PATH and file == base.CORE_VENV_DIR_NAME:
                        continue
                    remote_absolute_path = root + "/" + file
                    if checker.is_remote_dir(remote_absolute_path):
                        result.update(get_filenames_in_remote_dir(root=remote_absolute_path))
                    elif checker.is_remote_file(remote_absolute_path):
                        result.add(FilePath.from_filepath(
                            filepath=remote_absolute_path, project_folderpath=base.REMOTE_PROJECT_DIR_PATH,
                        ))
            except FileNotFoundError:
                raise exceptions.SSPDUnhandleableException(f"It isn't a folder in remote machine '{root}'")
            return result

        cls.REMOTE_FILES = get_filenames_in_remote_dir(base.REMOTE_PROJECT_DIR_PATH)
        cls.REMOTE_FILES.difference_update(base.IGNORE.files2ignore)

    @classmethod
    def refresh(cls):
        base.IGNORE.update_files2ignore()

        cls.reset_local_files()
        cls.reset_remote_files()

        cls.__updated_files = set()
        cls.__new_files = set()
        cls.__deleted_files = set()

    @classmethod
    def __is_file_updated(cls, filepath: FilePath) -> bool:
        local_filepath = filepath.to_absolute(base.LOCAL_PROJECT_DIR_PATH)
        remote_filepath = filepath.to_absolute(base.REMOTE_PROJECT_DIR_PATH)
        try:
            with open(local_filepath, "rb") as local_file:
                local_file_bytes = local_file.read()
            with base.SFTP_REMOTE_MACHINE.open(remote_filepath, "r") as remote_file:
                remote_file_bytes = remote_file.read()
            return is_byte_content_different(local_file_bytes, remote_file_bytes)
        except UnicodeDecodeError:
            return True

    @classmethod
    def get_updated_files(cls) -> set[FilePath]:
        if cls.__updated_files:
            return cls.__updated_files.copy()

        for filename in cls.REMOTE_FILES:
            if filename in cls.LOCAL_FILES and cls.__is_file_updated(filename):
                cls.__updated_files.add(filename)

        return cls.__updated_files.copy()

    @classmethod
    def get_new_files(cls) -> set[FilePath]:
        if cls.__new_files:
            return cls.__new_files.copy()

        for filename in cls.LOCAL_FILES:
            if filename not in cls.REMOTE_FILES:
                cls.__new_files.add(filename)

        return cls.__new_files.copy()

    @classmethod
    def get_deleted_files(cls) -> set[FilePath]:
        # TODO: you can look, that remote file not in local files (as in `new_files` but reversed)
        # but here is problem - remote project can create special files, so them will be always deleted
        return cls.__deleted_files.copy()
