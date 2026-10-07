class InitializationException(Exception):
    pass


class NotInitializedException(InitializationException):
    def __init__(self):
        super().__init__("SSPD project not initialized")


class ConnectionException(Exception):
    pass


class NotConnectedException(ConnectionException):
    def __init__(self):
        super().__init__("SSPD not connected to remote machine")


class RemoteCommandExecutionException(Exception):
    pass


class RemotePathException(RemoteCommandExecutionException):
    pass


class RemoteFileException(FileNotFoundError):
    pass


class LocalFileException(FileNotFoundError):
    pass


class CheckFailedException(InitializationException):
    pass
