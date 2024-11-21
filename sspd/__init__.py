import os
import paramiko
from sspd import __check_before_start, config_file, ignoring_file
import logging


logging.getLogger("paramiko").setLevel(logging.WARNING)
PROPERTIES_DIR = "sspd"
os.makedirs(PROPERTIES_DIR, exist_ok=True)


def close_connections():
    try:
        objects_to_close = [SSH_REMOTE_MACHINE, SFTP_REMOTE_MACHINE]
        for object_to_close in objects_to_close:
            try:
                object_to_close.close()
            except Exception:
                pass
    except Exception:
        pass


def exception(text: str):
    close_connections()
    print("SSPD-Exception:", text)
    input("Press ENTER...")
    os.abort()


# Get SSPD user settings
config = config_file.ConfigFile(os.path.join(PROPERTIES_DIR, "ProjectDelivery.ini"))
REMOTE_IPV4 = config.get_required_value(section="RemoteMachine", option="REMOTE_IPV4")
PASSWORD_TO_REMOTE_SERVER = config.get_required_value(section="RemoteMachine", option="PASSWORD_TO_REMOTE_SERVER")
REMOTE_USERNAME = config.get_required_value(section="RemoteMachine", option="REMOTE_USERNAME")
REMOTE_PROJECT_DIR_PATH = config.get_required_value(section="RemoteMachine", option="REMOTE_PROJECT_DIR_PATH")
while REMOTE_PROJECT_DIR_PATH.endswith("/"):
    REMOTE_PROJECT_DIR_PATH = REMOTE_PROJECT_DIR_PATH.removesuffix("/")
REMOTE_PROJECT_DIR_PATH = REMOTE_PROJECT_DIR_PATH.replace("~/", f"/{REMOTE_USERNAME}/")
REMOTE_SERVICE_FILENAME = config.get_required_value(section="RemoteMachine", option="REMOTE_SERVICE_FILENAME")
while REMOTE_SERVICE_FILENAME.startswith("/"):
    REMOTE_SERVICE_FILENAME = REMOTE_SERVICE_FILENAME.removeprefix("/")
if not REMOTE_SERVICE_FILENAME.endswith(".service"):
    REMOTE_SERVICE_FILENAME += ".service"
REMOTE_PATH_TO_SERVICES_DIR = "/etc/systemd/system/"
REMOTE_PROJECT_FILE_TO_RUN = config.get_required_value(section="RemoteMachine", option="REMOTE_PROJECT_FILE_TO_RUN")
REMOTE_VENV_DIR_NAME = config.get_required_value(section="RemoteMachine", option="REMOTE_VENV_DIR_NAME")
while REMOTE_VENV_DIR_NAME.startswith("/") or REMOTE_VENV_DIR_NAME.endswith("/"):
    REMOTE_VENV_DIR_NAME = REMOTE_VENV_DIR_NAME.removesuffix("/").removeprefix("/")
REMOTE_LOG_FILE_PATH = config.get_optional_value(section="RemoteMachine", option="REMOTE_LOG_FILE_PATH")
LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN = config.get_optional_value(section="LocalMachine", option="LOCAL_LOG_FILE_PATH_TO_DOWNLOAD_IN")
LOCAL_PROJECT_DIR_PATH = config.get_required_value(section="LocalMachine", option="LOCAL_PROJECT_DIR_PATH")
while LOCAL_PROJECT_DIR_PATH.endswith("/"):
    LOCAL_PROJECT_DIR_PATH = LOCAL_PROJECT_DIR_PATH.removesuffix("/")


# Get filepaths to ignore in SSPD process
IGNORE = ignoring_file.IgnoreFile(
    ignore_filepath=os.path.join(PROPERTIES_DIR, "ProjectDelivery.ign"),
    project_path=LOCAL_PROJECT_DIR_PATH
)
IGNORE.update_files2ignore()


# Init SSH
SSH_REMOTE_MACHINE = paramiko.SSHClient()
SSH_REMOTE_MACHINE.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    # Connect to server
    SSH_REMOTE_MACHINE.connect(
        hostname=REMOTE_IPV4,
        username=REMOTE_USERNAME,
        password=PASSWORD_TO_REMOTE_SERVER,
    )
except paramiko.AuthenticationException:
    exception("Invalid USERNAME or PASSWORD")

# Init SCP
SFTP_REMOTE_MACHINE = SSH_REMOTE_MACHINE.open_sftp()


DEFAULT_SERVICE_FILE_CONTENT = f"""[Unit]
Description={REMOTE_SERVICE_FILENAME.replace(".service", "")}
After=syslog.target
After=network.target

[Service]
WorkingDirectory={REMOTE_PROJECT_DIR_PATH}

User={REMOTE_USERNAME}
Group={REMOTE_USERNAME}

Type=simple
Restart=always
ExecStart={REMOTE_PROJECT_DIR_PATH}/{REMOTE_VENV_DIR_NAME}/bin/python3 {REMOTE_PROJECT_DIR_PATH}/{REMOTE_PROJECT_FILE_TO_RUN}

[Install]
WantedBy=multi-user.target"""


__check_before_start.check_local_project_dir()
__check_before_start.check_remote_project_dir()
__check_before_start.check_remote_venv()
__check_before_start.check_remote_service()
