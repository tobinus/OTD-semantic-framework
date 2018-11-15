import urllib.parse
import os
from dotenv import load_dotenv, find_dotenv


_cached_uri = None
_has_loaded_dotenv = False


def get_uri():
    global _cached_uri

    if _cached_uri is None:
        _cached_uri = _create_uri_from_env()

    return _cached_uri


def _create_uri_from_env():
    _ensure_loaded_dotenv()

    username = os.environ.get('DB_USERNAME', '')
    passwd = os.environ.get('DB_PASSWD', '')
    host = os.environ.get('DB_HOST', 'localhost')
    name = os.environ.get('DB_NAME', 'ontodb')

    return create_uri(username, passwd, host, name)


def _ensure_loaded_dotenv():
    global _has_loaded_dotenv

    if _has_loaded_dotenv:
        return

    dotenv_file = find_dotenv()
    if dotenv_file:
        print(f'Loading environment variables from "{dotenv_file}"')
        load_dotenv(dotenv_file)
    else:
        print(
            'No .env file found in this or any parent directory, relying on '
            'directly supplied environment variables only'
        )

    _has_loaded_dotenv = True


def create_uri(username, passwd, host, name):
    return 'mongodb://{}:{}@{}/{}'.format(
        urllib.parse.quote_plus(username),
        urllib.parse.quote_plus(passwd),
        host,
        name
    )
