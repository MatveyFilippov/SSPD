from functools import lru_cache
import hashlib
import logging
import shlex
from .. import core
from ..base import get_config, get_ignore_manager
from ..utils.paths import FilePath


log = logging.getLogger(__name__)


@lru_cache(maxsize=1_000)
def get_checksum(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()
    checksum = hashlib.md5()
    checksum.update(data)
    return checksum.hexdigest()


def get_local_file_checksum(filepath: FilePath) -> str:
    log.debug(f"Getting local '{filepath}' checksum")

    local_filepath = filepath.to_absolute(get_config().local_project.dir_path)
    local_file_bytes = core.get_file_bytes_from_local_machine(local_filepath)
    return get_checksum(local_file_bytes)


def get_remote_file_checksum_by_downloading(filepath: FilePath) -> str:
    log.debug(f"Getting remote '{filepath}' checksum (by downloading)")

    remote_filepath = filepath.to_absolute(get_config().remote_project.dir_path)
    remote_file_bytes = core.get_file_bytes_from_remote_machine(remote_filepath)
    return get_checksum(remote_file_bytes)


def get_remote_file_checksum_by_executing_command(filepath: FilePath) -> str:
    log.debug(f"Getting remote '{filepath}' checksum (by executing command)")

    remote_filepath = filepath.to_absolute(get_config().remote_project.dir_path)
    safe_remote_filepath = shlex.quote(remote_filepath)
    execution_response = core.execute_command_in_remote_machine(f"md5sum {safe_remote_filepath} | cut -d' ' -f1")
    return execution_response.message


def is_file_updated(filepath: FilePath) -> bool:  # TODO: optimize by checking file size
    return get_local_file_checksum(filepath) != get_remote_file_checksum_by_executing_command(filepath)


class FileAnalysing:
    LOCAL_FILES: set[FilePath] = set()
    REMOTE_FILES: set[FilePath] = set()

    __updated_files: set[FilePath] = set()
    __created_files: set[FilePath] = set()
    __deleted_files: set[FilePath] = set()

    @classmethod
    def reset_local_files(cls):
        log.debug("Resetting local files in FileAnalysing")

        local_project_dir_path = get_config().local_project.dir_path.rstrip("/")
        ignore_manager = get_ignore_manager()

        def get_filepaths_in_local_dir(root: str) -> set[FilePath]:
            result = set()
            for file in core.get_folder_listing_from_local_machine(root):
                filepath = FilePath.from_filepath(
                    filepath=(root + "/" + file),
                    project_folderpath=local_project_dir_path,
                )
                if ignore_manager.is_path_ignored(filepath.abstract):  # Check if ignored as file or parent folder
                    log.debug(f"Skip local (ignored as file or parent folder): '{filepath}'")
                    continue
                local_absolute_path = filepath.to_absolute(
                    project_folderpath=local_project_dir_path,
                )
                if core.is_local_folder(local_absolute_path):
                    if ignore_manager.is_path_ignored(filepath.abstract + "/"):  # Check if ignored as full folder
                        log.debug(f"Skip local (ignored as full folder): '{filepath}'")
                        continue
                    log.debug(f"Looking local folder: '{filepath}'")
                    result.update(get_filepaths_in_local_dir(root=local_absolute_path))
                elif core.is_local_file(local_absolute_path):
                    log.debug(f"Add local file: '{filepath}'")
                    result.add(filepath)
            return result

        cls.LOCAL_FILES = get_filepaths_in_local_dir(root=local_project_dir_path)

    @classmethod
    def reset_remote_files(cls):
        log.debug("Resetting remote files in FileAnalysing")

        remote_project_dir_path = get_config().remote_project.dir_path.rstrip("/")
        ignore_manager = get_ignore_manager()

        def get_filepaths_in_remote_dir(root: str) -> set[FilePath]:
            result = set()
            for file in core.get_folder_listing_from_remote_machine(root):
                filepath = FilePath.from_filepath(
                    filepath=(root + "/" + file),
                    project_folderpath=remote_project_dir_path,
                )
                if ignore_manager.is_path_ignored(filepath.abstract):  # Check if ignored as file or parent folder
                    log.debug(f"Skip remote (ignored as file or parent folder): '{filepath}'")
                    continue
                remote_absolute_path = filepath.to_absolute(
                    project_folderpath=remote_project_dir_path,
                )
                if core.is_remote_folder(remote_absolute_path):
                    if ignore_manager.is_path_ignored(filepath.abstract + "/"):  # Check if ignored as full folder
                        log.debug(f"Skip remote (ignored as full folder): '{filepath}'")
                        continue
                    log.debug(f"Looking remote folder: '{filepath}'")
                    result.update(get_filepaths_in_remote_dir(root=remote_absolute_path))
                elif core.is_remote_file(remote_absolute_path):
                    log.debug(f"Add remote file: '{filepath}'")
                    result.add(filepath)
            return result

        cls.REMOTE_FILES = get_filepaths_in_remote_dir(root=remote_project_dir_path)

    @classmethod
    def refresh(cls):
        log.debug("Refreshing FileAnalysing data")

        cls.__updated_files.clear()
        cls.__created_files.clear()
        cls.__deleted_files.clear()
        log.debug("Drop updated/created/deleted files cache")

        get_ignore_manager().reload()
        log.debug("Reload ignore manager")

        cls.reset_local_files()
        cls.reset_remote_files()

    @classmethod
    def get_updated_files(cls) -> set[FilePath]:
        if not cls.__updated_files:
            log.debug("Looking for updated files")
            for filepath in cls.REMOTE_FILES:
                if filepath in cls.LOCAL_FILES and is_file_updated(filepath):
                    cls.__updated_files.add(filepath)
        else:
            log.debug("Take updated files from cache")

        return cls.__updated_files.copy()

    @classmethod
    def get_created_files(cls) -> set[FilePath]:
        if not cls.__created_files:
            log.debug("Looking for created files")
            for filepath in cls.LOCAL_FILES:
                if filepath not in cls.REMOTE_FILES:
                    cls.__created_files.add(filepath)
        else:
            log.debug("Take created files from cache")

        return cls.__created_files.copy()

    @classmethod
    def get_deleted_files(cls) -> set[FilePath]:
        if not cls.__deleted_files:
            log.debug("Looking for deleted files")
            for filepath in cls.REMOTE_FILES:
                if filepath not in cls.LOCAL_FILES:
                    cls.__deleted_files.add(filepath)
        else:
            log.debug("Take deleted files from cache")

        return cls.__deleted_files.copy()
