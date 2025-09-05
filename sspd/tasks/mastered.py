from . import base
from .file_analysing import FileAnalysing
from .. import base as sspd_properties, checker
from ..misc_helpers import io
from ..misc_helpers.paths import FilePath
import os


def download_log_file():
    if checker.is_download_log_file_available():
        base.download_file_from_remote_server(
            remote_filepath=sspd_properties.REMOTE_LOG_FILE_PATH,
            local_filepath=sspd_properties.LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN,
        )


def send_files_from_project_dir(files: set[FilePath]):
    io.print_info("Start sending files from local to remote project dir")
    for file in files:
        local_filepath = file.to_absolute(sspd_properties.LOCAL_PROJECT_DIR_PATH)
        remote_filepath = file.to_absolute(sspd_properties.REMOTE_PROJECT_DIR_PATH)
        base.execute_remote_command(
            f"mkdir -p {os.path.dirname(remote_filepath)}", print_request=False, print_response=False,
        )
        base.send_file_to_remote_server(local_filepath, remote_filepath)
    io.print_info("All files are send to remote project dir")


def update_remote_code():
    io.print_info("Start updating remote code")

    io.print_info("Look differences in local and remote files")
    FileAnalysing.refresh()

    files2send = set()
    for new_file in FileAnalysing.get_new_files():
        files2send.add(new_file)
        io.print_info(f" * New: {files2send}")
    for updated_file in FileAnalysing.get_updated_files():
        files2send.add(updated_file)
        io.print_info(f" * Update: {updated_file}")
    if len(files2send) == 0:
        io.print_info("All files up to date!")
        return

    sign2break = "N"
    user_decision = input(f"Are you sure to send all this files to remote server? (y/{sign2break}): ")
    if user_decision.strip() == sign2break:
        io.print_info("Break process...")
        return

    base.stop_running_remote_code()
    send_files_from_project_dir(files2send)
    if base.REQUIREMENTS_FILE in files2send:
        base.run_reinstalling_remote_requirements()
    base.start_running_remote_code()

    io.print_info("All is done -> files in remote server are up to date!")
