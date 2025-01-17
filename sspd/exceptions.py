import sys


class SSPDException(SystemExit):
    def __init__(self, text: str):
        from .base import close_connections
        close_connections()
        print("SSPD-Exception:", text)
        input("Press ENTER...")
        sys.exit(-1)  # os.abort()
        # super().__init__(text)
