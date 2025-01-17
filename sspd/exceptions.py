import sys


class SSPDException(SystemExit):
    def __init__(self, text: str):
        close_connections()
        print("SSPD-Exception:", text)
        input("Press ENTER...")
        sys.exit(0)  # os.abort()
        # super().__init__(text)
