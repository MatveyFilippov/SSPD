import os
import paramiko
from .misc_helpers import config_file, ignoring_file
from . import exceptions


PROPERTIES_DIR = "SSPDFiles"
os.makedirs(PROPERTIES_DIR, exist_ok=True)


# Get SSPD user settings
config = config_file.ConfigFile(os.path.join(PROPERTIES_DIR, "ProjectDelivery.ini"))
REMOTE_USERNAME = config.get_required_value(section="RemoteMachine", option="REMOTE_USERNAME")
REMOTE_USER_HOME_DIR = f"/{REMOTE_USERNAME}/" if REMOTE_USERNAME == "root" else f"/home/{REMOTE_USERNAME}/"
tilda_replacer = lambda p: (REMOTE_USER_HOME_DIR + p.removeprefix("~/")) if p.startswith("~/") else p
REMOTE_IPV4 = config.get_required_value(section="RemoteMachine", option="REMOTE_IPV4")
PASSWORD_TO_REMOTE_SERVER = config.get_required_value(section="RemoteMachine", option="PASSWORD_TO_REMOTE_SERVER")
REMOTE_PROJECT_DIR_PATH = tilda_replacer(config.get_required_value(section="RemoteMachine", option="REMOTE_PROJECT_DIR_PATH"))
while REMOTE_PROJECT_DIR_PATH.endswith("/"):
    REMOTE_PROJECT_DIR_PATH = REMOTE_PROJECT_DIR_PATH.removesuffix("/")
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
if REMOTE_LOG_FILE_PATH:
    REMOTE_LOG_FILE_PATH = tilda_replacer(REMOTE_LOG_FILE_PATH)
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
    raise exceptions.SSPDExceptionWithoutClosingConnection("Invalid USERNAME or PASSWORD")

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
