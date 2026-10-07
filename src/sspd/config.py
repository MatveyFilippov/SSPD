from dataclasses import dataclass
from paramiko.config import SSH_PORT


@dataclass(frozen=True, slots=True)
class RemoteMachine:  # TODO: expand connection options
    username: str
    password: str
    host: str
    port: int = SSH_PORT
    reject_connection_if_unknown_host: bool = True


@dataclass(frozen=True, slots=True)
class RemoteProjectLifecycleByService:
    service_filename: str
    services_dir_path: str = "/etc/systemd/system"
    service_content: str | None = None  # If None, will use default content (TODO: link to default content)


@dataclass(frozen=True, slots=True)
class RemoteProject:
    dir_path: str
    lifecycle: RemoteProjectLifecycleByService | None  # TODO: add support for another managers


@dataclass(frozen=True, slots=True)
class LocalProject:
    dir_path: str


@dataclass(frozen=True, slots=True)
class PythonCore:
    venv_dir_name: str = ".venv"
    executable_file_name: str = "main.py"
    requirements_file_name: str | None = None


@dataclass(frozen=True, slots=True)
class Config:
    remote_machine: RemoteMachine
    remote_project: RemoteProject
    local_project: LocalProject
    core: PythonCore | None  # TODO: add support for projects in other programming languages
