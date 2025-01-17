import os
from .. import base, exceptions


def __write_default_service() -> str:  # TODO: put service file as superuser (nano M.service -> sudo nano M.service)
    service_filepath_created_by_base = os.path.join(
        base.PROPERTIES_DIR, "SSPD_DefaultServiceFileCreatedInRemoteMachine.service"
    )
    with open(service_filepath_created_by_base, "w") as default_service_file:
        default_service_file.write(base.DEFAULT_SERVICE_FILE_CONTENT)
    with open(service_filepath_created_by_base, "rb") as default_service_file:
        base.SFTP_REMOTE_MACHINE.putfo(
            default_service_file, base.REMOTE_PATH_TO_SERVICES_DIR + base.REMOTE_SERVICE_FILENAME
        )
    base.SSH_REMOTE_MACHINE.exec_command("sudo systemctl daemon-reload")
    base.SSH_REMOTE_MACHINE.exec_command(f"sudo systemctl enable {base.REMOTE_SERVICE_FILENAME}")
    base.SSH_REMOTE_MACHINE.exec_command(f"sudo systemctl start {base.REMOTE_SERVICE_FILENAME}")
    return service_filepath_created_by_base


def check_remote_project_dir():
    for i in range(2):
        _, _, stderr = base.SSH_REMOTE_MACHINE.exec_command(f"cd {base.REMOTE_PROJECT_DIR_PATH}")
        if "No such file or directory" in stderr.read().decode():
            if i == 0:
                base.SSH_REMOTE_MACHINE.exec_command(
                    f"mkdir -p {base.REMOTE_PROJECT_DIR_PATH}"
                )
            else:
                raise exceptions.SSPDUnhandlableException(
                    f"No working dir ('{base.REMOTE_PROJECT_DIR_PATH}') in remote server"
                )


def check_remote_venv():
    for i in range(2):
        _, _, stderr = base.SSH_REMOTE_MACHINE.exec_command(
            f"source {base.REMOTE_PROJECT_DIR_PATH}/{base.REMOTE_VENV_DIR_NAME}/bin/activate"
        )
        if "No such file or directory" in stderr.read().decode():
            if i == 0:
                print(f"Creating '{base.REMOTE_VENV_DIR_NAME}' in remote project dir...")
                _, _, stderr = base.SSH_REMOTE_MACHINE.exec_command(
                    f"python3 -m venv {base.REMOTE_PROJECT_DIR_PATH}/{base.REMOTE_VENV_DIR_NAME}"
                )
                er_text = stderr.read()
                if er_text:
                    raise exceptions.SSPDUnhandlableException(er_text)
            else:
                raise exceptions.SSPDUnhandlableException(
                    f"Virtual environment not exists in working dir '{base.REMOTE_PROJECT_DIR_PATH}'"
                )


def check_remote_service():
    try:
        with base.SFTP_REMOTE_MACHINE.open(base.REMOTE_PATH_TO_SERVICES_DIR + base.REMOTE_SERVICE_FILENAME, "r") as remote_file:
            if base.DEFAULT_SERVICE_FILE_CONTENT.strip() != remote_file.read().decode().strip():
                raise ValueError("Service file content is not actual")
    except FileNotFoundError:
        er_text = f"File '{base.REMOTE_SERVICE_FILENAME}' (service) not exists in remote server"
        print(er_text)
        sign2ignore = "N"
        user_decision = input(f"Can I write default service by myself (y/{sign2ignore}): ")
        if user_decision.strip() == sign2ignore:
            raise exceptions.SSPDUnhandlableException(er_text)
        local_service_cope_filepath = __write_default_service()
        print(f"You can look copy of created service file in '{local_service_cope_filepath}'")
    except ValueError:
        print(f"Content of '{base.REMOTE_SERVICE_FILENAME}' (service) is not actual in remote server")
        sign2ignore = "N"
        user_decision = input(f"Can I rewrite default service by myself (y/{sign2ignore}): ")
        if user_decision.strip() != sign2ignore:
            local_service_cope_filepath = __write_default_service()
            print(f"You can look copy of created service file in '{local_service_cope_filepath}'")
