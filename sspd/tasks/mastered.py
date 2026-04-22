from . import base
from .file_analysing import FileAnalysing
from .. import base as sspd_properties, checker, exceptions
from ..utils import io
from ..utils.paths import FilePath


def download_log_file_from_remote_machine():
    if checker.is_download_log_file_available():
        base.download_file_from_remote_machine(
            remote_filepath=sspd_properties.REMOTE_LOG_FILE_PATH,
            local_filepath=sspd_properties.LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN,
        )


def send_files_to_remote_project(files: set[FilePath]):
    io.print_info("Start sending files from local to remote project dir")
    for file in files:
        local_filepath = file.to_absolute(sspd_properties.LOCAL_PROJECT_DIR_PATH)
        remote_filepath = file.to_absolute(sspd_properties.REMOTE_PROJECT_DIR_PATH)
        base.send_file_to_remote_machine(local_filepath, remote_filepath)
    io.print_info("All files are send to remote project dir")


def delete_files_in_remote_project_dir(files: set[FilePath]):
    io.print_info("Start deleting files in remote project dir")
    for file in files:
        remote_filepath = file.to_absolute(sspd_properties.REMOTE_PROJECT_DIR_PATH)
        base.delete_file_in_remote_machine(remote_filepath)
    io.print_info("All files are delete in remote project dir")


def update_remote_project(run_after_update: bool = True):
    io.print_info("Start updating remote code")

    io.print_info("Look differences in local and remote files")
    FileAnalysing.refresh()

    files2send = set()
    files2delete = set()
    for created_file in FileAnalysing.get_created_files():
        files2send.add(created_file)
        io.print_info(f" * Create: {created_file}")
    for updated_file in FileAnalysing.get_updated_files():
        files2send.add(updated_file)
        io.print_info(f" * Update: {updated_file}")
    for deleted_file in FileAnalysing.get_deleted_files():
        files2delete.add(deleted_file)
        io.print_info(f" * Delete: {deleted_file}")
    if len(files2send) == 0 and len(files2delete) == 0:
        io.print_info("Remote project up to date!")
        return

    if io.input_bool("Are you sure to update remote project? (y/{sign2break}): ", sign2break="N"):
        io.print_info("Break process...")
        return

    status, response = base.stop_running_remote_service(raise_on_error=False)
    if status == -1:
        io.print_info("While stop running was unexpected error, do you want to break process?")
        if io.input_bool("ENTER (to continue) / '{sign2break}' (to break): ", sign2break="Br"):
            raise exceptions.SSPDUnhandleableException(response)

    if files2send:
        send_files_to_remote_project(files2send)
    if files2delete:
        delete_files_in_remote_project_dir(files2delete)

    if base.REQUIREMENTS_FILE in files2send:
        base.run_installing_requirements_in_remote_machine()

    if run_after_update:
        base.start_running_remote_service()

    io.print_info("All is done -> files in remote server are up to date!")
