from __future__ import print_function
import pymongo as pg
import requests
from pymongo.errors import AutoReconnect, ConnectionFailure
from notebook.utils import url_path_join


class Connection(object):
    """MongoDB connection wrapper at the front-end.

    This object establish connections to the given database. Error will be thrown if fails, otherwise push the database information to the server through REST API.
    """

    def __init__(self, dbHost="localhost", dbPort=27017, db="vis", sevrPort=None):
        """
        Args:
            dbHost(str): The host name or address. Defaults to ``localhost``.
            dbPort(int): The port that the specified database is listening to.
                Defaults to 27017.
            db: A MongoDB database to store or retrive data. Defaults to
                ``vis``.
            sevrPort(int): The port that Jupyter server listens on. Defaults to
                8888. By default the server is running on the localhost.

        Raises:
            Exception: If initiating connection to specified database fails.
        """
        self.host = dbHost
        self.port = dbPort
        self.sevrPort = 8888
        if sevrPort is not None and isinstance(sevrPort, int):
            self.sevrPort = sevrPort
        self._url = "http://localhost:{}/".format(self.sevrPort)
        try:
            self.client = pg.MongoClient(dbHost, dbPort)
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

    def rm_catalog(self, collection, db='vis'):
        """Remove all data associated with given catalog collection.

        Args:
            collection(str): The catalog collection to be removed.
            db(str): The database that the collections are stored. Defaults to
                ``vis``.
        """
        db = self.client[db]
        db.drop_collection(collection)
        db['mst'].delete_one({'_id':collection})
        db['healpix'].delete_one({'_id':collection})

    def rm_circles(self, circles_id, db='vis'):
        """Remove stored data for a CirclesOverLay.

        Args:
            circles_id(str): The name given to this particular CirclesOverLay.
            db(str): The database that the data is stored. Defaults to ``vis``.
        """
        db = self.client[db]
        db['circles'].delete_one({'_id':circles_id})

    def show_catalogs(self, db='vis'):
        """Show catalogs stored in a given database.

        Args:
            db(str): The MongoDB database to look for stored catalogs. Defaults
                to ``vis``.
        Returns:
            A list of catalog collection names.
        """
        reserved = ['mst', 'circles', 'healpix']  # reserved for other use
        catalogs = self.client[db].collection_names(include_system_collections=False)
        catalogs = [x for x in catalogs if x not in reserved]

        return catalogs

    def show_circles(self):
        """Show CirclesOverLay data stored in database.

        Returns:
            A list of CirclesOverLay ids.
        """
        circles = list(self.db['circles'].find({},{'_id':1}))
        circles = [x['_id'] for x in circles]

        return circles
