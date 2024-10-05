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


def get_file_name(file_path: str, with_extension=True) -> str:
    file_path = file_path.strip()
    if "/" in file_path:
        file_name = file_path.split("/")[-1]
    elif "\\" in file_path:
        file_name = file_path.split("\\")[-1]
    else:
        file_name = file_path

    if not with_extension and "." in file_name:
        file_name = file_name.split(".")[0]

    return file_name


def get_file_path_from_dir(from_dir_path: str, file_path: str) -> list[str]:
    result_path = file_path.replace(from_dir_path, "")
    while result_path.startswith("/") or result_path.startswith("\\"):
        result_path = result_path[1:]
    if "/" in result_path:
        result = result_path.split("/")
    elif "\\" in result_path:
        result = result_path.split("\\")
    else:
        result = [result_path]
    return result


def is_files_different(local: bytes, remote: bytes) -> bool:
    return get_checksum(local) != get_checksum(remote)
