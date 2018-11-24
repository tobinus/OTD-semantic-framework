import urllib.parse
import os
from utils.dotenv import ensure_loaded_dotenv
from pymongo import MongoClient


class MongoDBConnection:
    """
    Context manager for establishing MongoDB connections and closing them.

    Example:
        >>> with MongoDBConnection() as client:
        ...     db = client.ontodb
        ...     print([str(i) for i in db.ontologies.distinct('_id')])
        ...
        ['5bdaeb6e09b63846c5a02a7e']
    """

    def __init__(self, uri=None):
        """
        Create new context manager, which can be used to establish connections
        to a MongoDB instance.

        When used in the with statement, the MongoClient instance is returned.

        Args:
            uri: The mongodb:// uri used to establish a connection. If not
                given, it will be inferred from the environment variables using
                get_uri().

        See Also:
            get_uri()
        """
        if uri is None:
            uri = get_uri()
        self.uri = uri
        self.connection = None

    def __enter__(self):
        self.connection = MongoClient(self.uri)
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()


_cached_uri = None


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
    ensure_loaded_dotenv()

    username = os.environ.get('DB_USERNAME', '')
    passwd = os.environ.get('DB_PASSWD', '')
    host = os.environ.get('DB_HOST', 'localhost')
    name = os.environ.get('DB_NAME', 'ontodb')

    return create_uri(username, passwd, host, name)


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
