import hashlib


def get_checksum(data: str | bytes) -> str:
    if type(data) == str:
        data = data.encode()
    checksum = hashlib.md5()
    checksum.update(data)
    return checksum.hexdigest()


def print_request(text: str):
    print("Local:", text)


def print_response(text: str):
    print("Remote:", text)


def is_byte_content_different(local: bytes, remote: bytes) -> bool:
    return get_checksum(local) != get_checksum(remote)
