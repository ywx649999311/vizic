import pymongo as pg
import requests
from pymongo.errors import AutoReconnect, ConnectionFailure
from notebook.utils import url_path_join


class Connection(object):
    """MongoDB connection wrapper at the front-end."""

    def __init__(self, host="localhost", port=27017, db="vis", url='http://localhost:8888/'):
        """Initiate a connection to the database with provided information.

        Args:
            host(str): The host name or address.
            port(int): The port that the specified database is listening to.
            db: A MongoDB database to store or retrive data.
            url(str): The address for the Jupyter server. This can be determined
                using ``NotebookUrl`` widget is not known.

        Raises:
            Exception: If initiating connection to specified database fails.
        """
        self.host = host
        self.port = port
        self._url = url
        try:
            self.client = pg.MongoClient(host, port)
            self.db = self.client[db]
            self.change_db(db)
        except ConnectionFailure as err:
            print('Error: Connection to MongoDB instance is refused!')
            raise Exception('Check database info before initialize connection!')

    def change_db(self, db):
        """Change the database used for ``Vizic``"""
        self.db = self.client[db]
        body = {
            'host': self.host,
            'port': self.port,
            'db': db
        }
        path = url_path_join(self._url, '/connection/')
        req = requests.post(path, data=body)
        if req.status_code != 200:
            raise Exception('Change database failed!')
