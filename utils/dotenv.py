import sys
from dotenv import load_dotenv, find_dotenv


_has_loaded_dotenv = False


def ensure_loaded_dotenv():
    """
    Ensure that any .env files have been loaded.
    """
    global _has_loaded_dotenv

    if _has_loaded_dotenv:
        return

    dotenv_file = find_dotenv()
    if dotenv_file:
        print(
            f'Loading environment variables from "{dotenv_file}"',
            file=sys.stderr
        )
        load_dotenv(dotenv_file)
    else:
        print(
            'No .env file found in this or any parent directory, relying on '
            'directly supplied environment variables only',
            file=sys.stderr
        )

    _has_loaded_dotenv = True
