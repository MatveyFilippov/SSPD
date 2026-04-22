from .. import base, exceptions
from ..utils import io
import os
from stat import S_ISDIR, S_ISREG


def is_remote_dir(path: str) -> bool:
    try:
        file_attr = base.SFTP_REMOTE_MACHINE.stat(path)
        return S_ISDIR(file_attr.st_mode)
    except IOError:
        return False


def is_remote_file(path: str) -> bool:
    try:
        file_attr = base.SFTP_REMOTE_MACHINE.stat(path)
        return S_ISREG(file_attr.st_mode)
    except IOError:
        return False


def __write_service(local_content_filepath: str | None = None) -> str:  # TODO: put service file as superuser (nano M.service -> sudo nano M.service)
    if not local_content_filepath:
        local_content_filepath = os.path.join(base.PROPERTIES_DIR, "SSPD_CopyOfCreatedServiceInRemoteMachine.service")
        with open(local_content_filepath, "w") as service_file:
            service_file.write(base.SERVICE_CONTENT)
    with open(local_content_filepath, "rb") as service_file:
        base.SFTP_REMOTE_MACHINE.putfo(service_file, base.REMOTE_PATH_TO_SERVICES_DIR + base.REMOTE_SERVICE_FILENAME)
    base.SSH_REMOTE_MACHINE.exec_command("sudo systemctl daemon-reload")
    base.SSH_REMOTE_MACHINE.exec_command(f"sudo systemctl enable {base.REMOTE_SERVICE_FILENAME}")
    return local_content_filepath


def check_remote_project_dir():
    if not is_remote_dir(base.REMOTE_PROJECT_DIR_PATH):
        base.SSH_REMOTE_MACHINE.exec_command(f"mkdir -p {base.REMOTE_PROJECT_DIR_PATH}")
        if not is_remote_dir(base.REMOTE_PROJECT_DIR_PATH):
            raise exceptions.SSPDUnhandleableException(
                f"No working dir ('{base.REMOTE_PROJECT_DIR_PATH}') in remote server"
            )


def check_remote_venv():
    for i in range(2):
        _, _, stderr = base.SSH_REMOTE_MACHINE.exec_command(
            f"source {base.REMOTE_PROJECT_DIR_PATH}/{base.CORE_VENV_DIR_NAME}/bin/activate"
        )
        if "No such file or directory" in stderr.read().decode():
            if i == 0:
                io.print_info(f"Creating '{base.CORE_VENV_DIR_NAME}' in remote project dir...")
                _, _, stderr = base.SSH_REMOTE_MACHINE.exec_command(
                    f"python3 -m venv {base.REMOTE_PROJECT_DIR_PATH}/{base.CORE_VENV_DIR_NAME}"
                )
                er_text = stderr.read()
                if er_text:
                    raise exceptions.SSPDUnhandleableException(er_text)
            else:
                raise exceptions.SSPDUnhandleableException(
                    f"Virtual environment not exists in working dir '{base.REMOTE_PROJECT_DIR_PATH}'"
                )


def check_remote_service():
    try:
        with base.SFTP_REMOTE_MACHINE.open(base.REMOTE_PATH_TO_SERVICES_DIR + base.REMOTE_SERVICE_FILENAME, "r") as remote_file:
            if base.SERVICE_CONTENT != remote_file.read().decode().strip():
                raise ValueError("Service file content is not actual")
    except FileNotFoundError:
        er_text = f"File '{base.REMOTE_SERVICE_FILENAME}' (service) not exists in remote server"
        io.print_info(er_text)
        if io.input_bool("Can I write service by myself (y/{sign2ignore}): ", sign2ignore="N"):
            raise exceptions.SSPDUnhandleableException(er_text)
        local_service_copy_filepath = __write_service(local_content_filepath=base.LOCAL_SERVICE_CONTENT_PATH)
        io.print_info(f"You can look copy of created service file in '{local_service_copy_filepath}'")
    except ValueError:
        io.print_info(f"Content of '{base.REMOTE_SERVICE_FILENAME}' (service) is not actual in remote server")
        if not io.input_bool("Can I rewrite service by myself (y/{sign2ignore}): ", sign2ignore="N"):
            local_service_copy_filepath = __write_service(local_content_filepath=base.LOCAL_SERVICE_CONTENT_PATH)
            io.print_info(f"You can look copy of created service file in '{local_service_copy_filepath}'")
