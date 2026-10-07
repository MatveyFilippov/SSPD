import logging
import paramiko
from ..config import RemoteMachine
from ..exceptions import ConnectionException, NotConnectedException


log = logging.getLogger(__name__)

__SSH: paramiko.SSHClient | None = None
__SFTP: paramiko.SFTPClient | None = None


def open_connection(remote_machine_config: RemoteMachine):
    global __SSH
    log.debug("Opening connection")

    if __SSH is not None:
        raise ConnectionException("Connection is already open")

    temp_ssh = paramiko.SSHClient()

    temp_ssh.load_system_host_keys()
    temp_ssh.set_missing_host_key_policy(
        paramiko.RejectPolicy
        if remote_machine_config.reject_connection_if_unknown_host else
        paramiko.WarningPolicy
    )

    temp_ssh.connect(  # TODO: catch and process possible errors
        hostname=remote_machine_config.host,
        port=remote_machine_config.port,
        username=remote_machine_config.username,
        password=remote_machine_config.password,
    )

    __SSH = temp_ssh
    log.info(f"Open connection to {remote_machine_config.username}@{remote_machine_config.host}")


def get_ssh() -> paramiko.SSHClient:
    global __SSH
    if __SSH is None:
        raise NotConnectedException()
    return __SSH


def get_sftp() -> paramiko.SFTPClient:
    global __SFTP
    if __SFTP is None:
        __SFTP = get_ssh().open_sftp()
    return __SFTP


def close_connection():
    global __SFTP, __SSH
    for object_to_close in [__SFTP, __SSH]:
        try:
            object_to_close.close()
        except Exception:  # Object can be null or close is not available
            pass
    log.info("Close connection")
