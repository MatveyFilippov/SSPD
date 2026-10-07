import logging
from .config import Config
from .exceptions import InitializationException, NotInitializedException
from .core import open_connection, close_connection
from .utils.ignore_manager import IgnoreManager, SimpleIgnoreManager
from . import _checkers


log = logging.getLogger("sspd")


__CONFIG: Config | None = None
__IGNORE_MANAGER: IgnoreManager | None = None


def initialize(config: Config, ignore_manager: IgnoreManager = None):
    global __CONFIG, __IGNORE_MANAGER

    log.debug("Starting initialize")

    if __CONFIG is not None:
        raise InitializationException("Already initialized, call clean() to drop configuration and close connection")

    __CONFIG = config
    log.debug("Set configuration")

    __IGNORE_MANAGER = ignore_manager
    log.debug("Set ignore manager" if ignore_manager else "No ignore manager, no files will be ignored")

    log.debug("Checking local project and core config data")
    _checkers.check_local(
        local_project_config=__CONFIG.local_project,
        local_core_config=__CONFIG.core,
    )

    open_connection(remote_machine_config=__CONFIG.remote_machine)

    log.debug("Checking remote project and core config data")
    _checkers.check_remote(
        remote_project_config=__CONFIG.remote_project,
        remote_core_config=__CONFIG.core,
    )

    log.info("Successfully initialize")


def get_config() -> Config:
    global __CONFIG
    if __CONFIG is None:
        raise NotInitializedException()
    return __CONFIG


def get_ignore_manager() -> IgnoreManager:
    global __IGNORE_MANAGER
    if __IGNORE_MANAGER is None:
        __IGNORE_MANAGER = SimpleIgnoreManager(patterns=[])
    return __IGNORE_MANAGER


def clean():
    global __CONFIG, __IGNORE_MANAGER
    if __CONFIG is not None:
        close_connection()
        __CONFIG = None
    __IGNORE_MANAGER = None

    log.info("Successfully clean")
