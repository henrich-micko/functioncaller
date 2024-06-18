import string
import secrets


def generate_char_code(lenght: int) -> str:
    return ''.join(
        secrets.choice(string.ascii_uppercase + string.digits)
        for _ in range(lenght)
    )
