from __future__ import print_function
import requests
from pymongo.errors import AutoReconnect, ConnectionFailure
from notebook.utils import url_path_join
import numpy as np
import pandas as pd
import pymongo as pmg


class Collection(object):

    def __init__(self):
        self.point = False
        self.radius = False
        self.name = ''
        self._des_crs = []
        self.x_range = 0
        self.y_range = 0
        self.db_maxZoom = 8
        self._minMax = {}
        self.cat_ct = 1


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
            self.client = pmg.MongoClient(dbHost, dbPort)
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

    def import_new(self, df, coll_name, map_dict=None):

        exist_colls = self.show_catalogs()
        if coll_name in exist_colls:
            raise Exception('Provided collection name already exists, use a different name or use function import_exists().')

        coll = Collection()
        coll.name = coll_name

        if map_dict is not None:
            for k in map_dict.keys():
                df[k] = df[map_dict[k]]

        clms = [x.upper() for x in list(df.columns)]
        if not set(['RA', 'DEC']).issubset(set(clms)):
            raise Exception("RA, DEC is required for visualization!")
        if not set(['A_IMAGE', 'B_IMAGE', 'THETA_IMAGE']).issubset(set(clms)):
            print('No shape information provided')
            if 'RADIUS' in clms:
                print('Will use radius for filtering!')
                coll.radius = True
            else:
                print('Object as point, slow performance!')
                coll.point = True
        df_r, coll._des_crs = self._data_prep(df, coll)
        coll.x_range = coll._des_crs[2]*256
        coll.y_range = coll._des_crs[3]*256

        # drop created mapped columns before ingecting data
        if map_dict is not None:
            col_keys = [x.upper() for x in map_dict.keys()
                        if x.upper() not in ['RA', 'DEC']]
            df_r.drop(col_keys,axis=1, inplace=True)
            for k in col_keys:
                coll._minMax.pop(k, None)

        self._insert_data(df_r, coll)

    def add_to_old(self, df, coll_name, map_dict=None):

        exist_colls = self.show_catalogs()
        if coll_name in exist_colls:
            db_meta = self.read_meta(coll_name)
        else:
            raise Exception('Provided collection name does not exist, please use function import_new()')

        coll = Collection()
        coll.name = coll_name
        if map_dict is not None:
            for k in map_dict.keys():
                df[k] = df[map_dict[k]]
        print(list(df.columns))
        clms = [x.upper() for x in list(df.columns)]
        if not set(['RA', 'DEC']).issubset(set(clms)):
            raise Exception("RA, DEC is required for visualization!")
        if set(['A_IMAGE', 'B_IMAGE', 'THETA_IMAGE']).issubset(set(clms)) and \
                (not db_meta.radius and not db_meta.point):
            print('Will use shape information for filtering')
        elif ('RADIUS' not in clms and
                not set(['A_IMAGE', 'B_IMAGE', 'THETA_IMAGE']).issubset(set(clms))) or  \
                db_meta.point:
            print(db_meta.point)
            coll.point = True
            print('Objects as points, slow performance')
        else:
            coll.radius = True
            print('Use raidus to filter objects')
        df_r, coll._des_crs = self._data_prep(df, coll)
        coll.x_range = coll._des_crs[2]*256
        coll.y_range = coll._des_crs[3]*256
        self._update_coll(coll, db_meta)

        # drop created mapped columns before ingecting data
        if map_dict is not None:
            col_keys = [x.upper() for x in map_dict.keys()
                        if x.upper() not in ['RA', 'DEC']]
            df_r.drop(col_keys, axis=1, inplace=True)
            for k in col_keys:
                coll._minMax.pop(k, None)

        self._insert_data(df_r, coll)

    def _update_coll(self, new, old):

        xMin = new._des_crs[0] if new._des_crs[0] < old._des_crs[0] \
            else old._des_crs[0]
        xMax = new._des_crs[0]+new.x_range if new._des_crs[0]+new.x_range > \
            old._des_crs[0]+old.x_range else old._des_crs[0]+old.x_range
        yMin = new._des_crs[1]-new.y_range if new._des_crs[1]-new.y_range < \
            old._des_crs[1]-old.y_range else old._des_crs[1]-old.y_range
        yMax = new._des_crs[1] if new._des_crs[1] > old._des_crs[1] \
            else old._des_crs[1]

        new.x_range = xMax - xMin
        new.y_range = yMax - yMin
        new._des_crs = [xMin, yMax, new.x_range/256, new.y_range/256]

        com_keys = list(set(new._minMax.keys()) & set(old._minMax.keys()))
        for key in com_keys:
            nMin = new._minMax[key][0] if new._minMax[key][0] < \
                old._minMax[key][0] else old._minMax[key][0]
            nMax = new._minMax[key][1] if new._minMax[key][1] > \
                old._minMax[key][1] else old._minMax[key][1]
            new._minMax[key] = [nMin, nMax]

        for k in old._minMax.keys():
            if k not in com_keys:
                new._minMax[k] = old._minMax[k]
        new.cat_ct = old.cat_ct + 1

    def read_meta(self, coll_name):

        coll = Collection()
        meta = self.db[coll_name].find_one({'_id': 'meta'})
        coll.name = coll_name
        coll._des_crs = meta['adjust']
        coll.x_range = meta['xRange']
        coll.y_range = meta['yRange']
        coll._minMax = meta['minmax']
        coll.cat_ct = meta['catCt']
        (coll.radius, coll.point) = (meta['radius'], meta['point'])

        return coll

    def _data_prep(self, df, coll):
        """Private method for formatting catalog.

        Metadata for catalog provided in a pandas dataframe is extracted here.
        Corresponding tile ID for each object in the catalog is caculated and
        inserted into the dataframe, so as the mapped coordinates and
        shapes/sizes for the objects.

        Args:
            df: A pandas dataframe containning the catalog.
            coll: The Collection object containing meta information for the new
                catalog.

        Returns:
            A new pandas dataframe with added columns and a list specifying
            the coordinate scale.

        """
        dff = df.copy()
        dff.columns = [x.upper() for x in dff.columns]
        (xMax, xMin) = (dff['RA'].max(), dff['RA'].min())
        (yMax, yMin) = (dff['DEC'].max(), dff['DEC'].min())
        x_range = xMax - xMin
        y_range = yMax - yMin

        # find field min and max
        for col in dff.columns:
            if dff[col].dtype.kind == 'f':
                coll._minMax[col] = [dff[col].min(), dff[col].max()]

        if coll.radius:
            dff.loc[:, 'b'] = dff.loc[:, 'RADIUS'].apply(lambda x: x*0.267/3600)
            dff['theta'] = 0
        elif coll.point:
            dff['b'] = 360
            dff['theta'] = 0
        else:
            dff.loc[:, 'a'] = dff.loc[:, 'A_IMAGE'].apply(lambda x: x*0.267/3600)
            dff.loc[:, 'b'] = dff.loc[:, 'B_IMAGE'].apply(lambda x: x*0.267/3600)
            dff.loc[:, 'theta'] = dff.loc[:, 'THETA_IMAGE']

        # assign 'loc' columns for geoIndex in Mongo
        dff['loc'] = list(zip(dff.RA, dff.DEC))

        xScale = x_range/256
        yScale = y_range/256
        return dff, [xMin, yMax, xScale, yScale]

    def _insert_data(self, df, coll):
        """Private method to insert a catalog into database.

        Args:
            df: A pandas dataframe with correctly formatted catalog.
            coll_name: MongoDB collection name for the new catalog.
        """

        df['cat_rank'] = coll.cat_ct
        data_d = df.to_dict(orient='records')
        collection = self.db[coll.name]
        collection.insert_many(data_d, ordered=False)
        collection.update_one({'_id': 'meta'}, {'$set':{'adjust': coll._des_crs, 'xRange': coll.x_range, 'yRange': coll.y_range, 'minmax': coll._minMax, 'radius':coll.radius,'point':coll.point, 'catCt':coll.cat_ct}}, upsert=True)
        collection.create_index([('loc', pmg.GEO2D)], name='geo_loc_2d', min=-90, max=360)
        collection.create_index([('b', pmg.ASCENDING)], name='semi_axis')
