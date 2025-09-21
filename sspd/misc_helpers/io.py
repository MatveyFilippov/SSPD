# TODO: here is a lot of print --- make it as param echo=True & add log_echo=False


def input_bool(formatable_text: str, **for_true: str) -> bool:
    if len(for_true) != 1:
        raise ValueError("Kvarg 'for_true' must contain only one item")
    return input(formatable_text.format(**for_true)).strip() == list(for_true.values())[0]


def print_info(text: str):
    print(text)


def print_request(text: str):
    print("Local:", text)


def print_response(text: str):
    print("Remote:", text)
