import urllib.parse
import os
from dotenv import load_dotenv, find_dotenv


_cached_uri = None
_has_loaded_dotenv = False


def get_uri():
    """
    Obtain a default URI for connecting to MongoDB.

    This uses the environment variables given to the application, as well as any
    placed in .env files. The environment variables used are:
    * DB_USERNAME
    * DB_PASSWD
    * DB_HOST
    * DB_NAME (name of database to use)

    Returns:
        URI to be used with MongoClient's constructor, to connect to the
        database configured by the user.

    """
    global _cached_uri

    if _cached_uri is None:
        _cached_uri = _create_uri_from_env()

    return _cached_uri


def _create_uri_from_env():
    """
    Create a default URI using environment variables.

    This function does the actual work, while get_uri() simply handles caching
    of the created URI.

    Returns:
        URI to be used with MongoClient's constructor, to connect to the
        database configured by the user.
    """
    _ensure_loaded_dotenv()

    username = os.environ.get('DB_USERNAME', '')
    passwd = os.environ.get('DB_PASSWD', '')
    host = os.environ.get('DB_HOST', 'localhost')
    name = os.environ.get('DB_NAME', 'ontodb')

    return create_uri(username, passwd, host, name)


def _ensure_loaded_dotenv():
    """
    Ensure that any .env files have been loaded.
    """
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
    """
    Create a mongodb:// URI using the given details.

    Args:
        username: Username to authenticate with. Will be escaped.
        passwd: Password to authenticate with. Will be escaped.
        host: Host where the database can be found, optionally with a port.
        name: Name of the database to connect to.

    Returns:
        URI to be used with MongoClient's constructor, to connect to the
        database on the given host with the given username and password, using
        the given database name.
    """
    return 'mongodb://{}:{}@{}/{}'.format(
        urllib.parse.quote_plus(username),
        urllib.parse.quote_plus(passwd),
        host,
        name
    )
