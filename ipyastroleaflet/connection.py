import pymongo as pg
import requests
from pymongo.errors import AutoReconnect, ConnectionFailure
class Connection:

    def __init__(self, host="localhost", port=27017, db="vis", url='http://localhost:8888/'):

        self.host = host
        self.port = port
        self.__url = url
        try:
            self.client = pg.MongoClient(host, port)
            self.db = self.client[db]
            self.change_db(db)
        except ConnectionFailure as err:
            print ('Error: Connection to MongoDB instance is refused!')
            raise Exception('Check database info before initialize connection!')

    def change_db(self, db):

        self.db = self.client[db]
        body = {
            'host':self.host,
            'port':self.port,
            'db':db
        }
        path = self.__url+'connection/'
        req = requests.post(path, data=body)
        if req.status_code != 200:
            raise Exception('Change database failed!')
