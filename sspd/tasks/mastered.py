import os
from . import base
from .file_analysing import FileAnalysing
from .. import checker, misc_helpers
from .. import base as sspd_properties


# TODO: here is a lot of print --- make it as param echo=True & add log_echo=False


def download_log_file():
    if checker.is_download_log_file_available():
        base.download_file_from_remote_server(
            remote_filepath=sspd_properties.REMOTE_LOG_FILE_PATH,
            local_filepath=sspd_properties.LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN,
        )


def send_files_from_project_dir(filenames: set[str]):
    misc_helpers.print_request("Start sending files from local to remote project dir")
    for filename in filenames:
        local_filepath = os.path.join(sspd_properties.LOCAL_PROJECT_DIR_PATH, filename)
        remote_filepath = sspd_properties.REMOTE_PROJECT_DIR_PATH + "/" + filename
        base.execute_remote_command(f"mkdir -p {os.path.dirname(remote_filepath)}")
        base.send_file_to_remote_server(local_filepath, remote_filepath)
    misc_helpers.print_response("All files are send to remote project dir")


def update_remote_code():
    print("Start updating remote code")
    FileAnalysing.FILENAMES_TO_IGNORE.add(sspd_properties.REMOTE_VENV_DIR_NAME)
    FileAnalysing.refresh()
    print("Look differences in local and remote files")
    files2send = set()
    for new_file in FileAnalysing.get_new_files():
        if new_file in sspd_properties.IGNORE.files2ignore:
            continue
        files2send.add(new_file)
        print(" * New:", new_file)
    for updated_file in FileAnalysing.get_updated_files():
        if updated_file in sspd_properties.IGNORE.files2ignore:
            continue
        files2send.add(updated_file)
        print(" * Update:", updated_file)
    if len(files2send) == 0:
        print("All files up to date!")
        return
    sign2break = "N"
    user_decision = input(f"Are you sure to send all this files to remote server? (y/{sign2break}): ")
    if user_decision.strip() == sign2break:
        print("Break process...")
        return
    print()

    base.stop_running_remote_code()
    send_files_from_project_dir(files2send)
    if "requirements.txt" in files2send:
        base.run_reinstalling_remote_requirements()
    base.start_running_remote_code()
    print()

    print("All is done -> files in remote server are up to date!")
