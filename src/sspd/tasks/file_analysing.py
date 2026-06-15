from functools import lru_cache
import hashlib
import os
from . import base
from .. import base as sspd_properties, checker, exceptions
from ..utils.paths import FilePath


@lru_cache(maxsize=1_000)
def get_checksum(data: str | bytes) -> str:
    if type(data) == str:
        data = data.encode()
    checksum = hashlib.md5()
    checksum.update(data)
    return checksum.hexdigest()


def is_byte_content_different(local: bytes, remote: bytes) -> bool:
    return get_checksum(local) != get_checksum(remote)


def get_local_file_checksum(filepath: FilePath) -> str:
    local_filepath = filepath.to_absolute(sspd_properties.LOCAL_PROJECT_DIR_PATH)
    with open(local_filepath, "rb") as local_file:
        local_file_bytes = local_file.read()
    return get_checksum(local_file_bytes)


def get_remote_file_checksum_by_downloading(filepath: FilePath) -> str:
    remote_filepath = filepath.to_absolute(sspd_properties.REMOTE_PROJECT_DIR_PATH)
    with sspd_properties.SFTP_REMOTE_MACHINE.open(remote_filepath, "r") as remote_file:
        remote_file_bytes = remote_file.read()
    return get_checksum(remote_file_bytes)


def get_remote_file_checksum_by_executing_command(filepath: FilePath) -> str:
    remote_filepath = filepath.to_absolute(sspd_properties.REMOTE_PROJECT_DIR_PATH).replace("'", "'\\''")
    _, response = base.execute_command_in_remote_machine(
        command=f"md5sum '{remote_filepath}' | cut -d' ' -f1",
        raise_on_error=True, print_request=False, print_response=False,
    )
    return response


def is_file_updated(filepath: FilePath) -> bool:
    return get_local_file_checksum(filepath) != get_remote_file_checksum_by_executing_command(filepath)


class FileAnalysing:
    CORE_VENV_FILEPATH = FilePath(sspd_properties.CORE_VENV_DIR_NAME)
    LOCAL_FILES: set[FilePath] = set()
    REMOTE_FILES: set[FilePath] = set()

    __updated_files: set[FilePath] = set()
    __created_files: set[FilePath] = set()
    __deleted_files: set[FilePath] = set()

    @classmethod
    def reset_local_files(cls):
        cls.LOCAL_FILES = set()
        for current_dir, subdirs, files in os.walk(sspd_properties.LOCAL_PROJECT_DIR_PATH):
            kept_subdirs = []
            for subdir in subdirs:
                filepath = FilePath.from_filepath(
                    filepath=os.path.join(current_dir, subdir),
                    project_folderpath=sspd_properties.LOCAL_PROJECT_DIR_PATH,
                )
                if not sspd_properties.IGNORE.is_path_ignored(filepath) and filepath != cls.CORE_VENV_FILEPATH:
                    kept_subdirs.append(subdir)
            subdirs[:] = kept_subdirs

            for file in files:
                filepath = FilePath.from_filepath(
                    filepath=os.path.join(current_dir, file),
                    project_folderpath=sspd_properties.LOCAL_PROJECT_DIR_PATH,
                )
                if not sspd_properties.IGNORE.is_path_ignored(filepath):
                    cls.LOCAL_FILES.add(filepath)

    @classmethod
    def reset_remote_files(cls):
        def get_filepaths_in_remote_dir(root: str) -> set[FilePath]:
            result = set()
            try:
                for file in sspd_properties.SFTP_REMOTE_MACHINE.listdir(root):
                    filepath = FilePath.from_filepath(
                        filepath=(root + "/" + file),
                        project_folderpath=sspd_properties.REMOTE_PROJECT_DIR_PATH,
                    )
                    if sspd_properties.IGNORE.is_path_ignored(filepath) or filepath == cls.CORE_VENV_FILEPATH:
                        continue
                    remote_absolute_path = filepath.to_absolute(
                        project_folderpath=sspd_properties.REMOTE_PROJECT_DIR_PATH,
                    )
                    if checker.is_remote_dir(remote_absolute_path):
                        result.update(get_filepaths_in_remote_dir(root=remote_absolute_path))
                    elif checker.is_remote_file(remote_absolute_path):
                        result.add(filepath)
            except FileNotFoundError:
                raise exceptions.SSPDUnhandleableException(f"It isn't a folder in remote machine '{root}'")
            return result

        cls.REMOTE_FILES = get_filepaths_in_remote_dir(sspd_properties.REMOTE_PROJECT_DIR_PATH)

    @classmethod
    def refresh(cls):
        sspd_properties.IGNORE.update_ignore_patterns()

        cls.reset_local_files()
        cls.reset_remote_files()

        cls.__updated_files = set()
        cls.__created_files = set()
        cls.__deleted_files = set()

    @classmethod
    def get_updated_files(cls) -> set[FilePath]:
        if not cls.__updated_files:
            for filepath in cls.REMOTE_FILES:
                if filepath in cls.LOCAL_FILES and is_file_updated(filepath):
                    cls.__updated_files.add(filepath)

        return cls.__updated_files.copy()

    @classmethod
    def get_created_files(cls) -> set[FilePath]:
        if not cls.__created_files:
            for filepath in cls.LOCAL_FILES:
                if filepath not in cls.REMOTE_FILES:
                    cls.__created_files.add(filepath)

        return cls.__created_files.copy()

    @classmethod
    def get_deleted_files(cls) -> set[FilePath]:
        if not cls.__deleted_files:
            for filepath in cls.REMOTE_FILES:
                if filepath not in cls.LOCAL_FILES:
                    cls.__deleted_files.add(filepath)

        return cls.__deleted_files.copy()
