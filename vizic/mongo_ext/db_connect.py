import motor
from tornado import gen
import concurrent.futures as cfs
import time
from pymongo import MongoClient
from bson.json_util import dumps
# executor = cfs.ThreadPoolExecutor(max_workers=20)


class MongoConnect(object):
    """MongoDB utility wrapper.

    Attributes:
        range_dict(dict): Geographical coverage, represented as the value ranges
            in ``RA`` and ``DEC``, for catalog collections displayed in the notebooks.
        zoom_dict(dict): Maximum zooms for catalog collections displayed in
            Jupyter notebooks.
    """
    range_dict = {}
    zoom_dict = {}

    def __init__(self, host, port, db):
        """Initiate an asynchronous client and a static client.

        Args:
            host(str): MongoDB host name or address.
            port(int): The port number that MongoDB listens to.
            db(str): MongoDB database name for storing and retriving data.
        """
        self.client = motor.motor_tornado.MotorClient(host, port)
        self.db = self.client[db]
        self.stat_client = MongoClient(host, port)
        self.stat_db = self.stat_client[db]

    def close(self):
        """Close existing clients."""
        self.client.close()
        self.stat_client.close()

    @gen.coroutine
    def getTileData(self, coll, xc, yc, zoom):
        """Query the database for catalog in a particular tile.

        Args:
            coll(str): A user-defined or automatically generated MongoDB
                collection name for a specific catalog.
            xc(int): x-coordinate the required tile.
            yc(int): y-coordinate the required tile.
            zoom(int): Zoom level for the required tile.

        """
        # multiThread is not stable
        result = self.getCoordRange(xc, yc, zoom, self.zoom_dict[coll])
        minR = self.getMinRadius(zoom, self.range_dict[coll])
        cursor = self.db[coll].find({

            '$and': [
                {'tile_x': {"$lt":result[0]}},
                {'tile_x': {"$gt":result[1]}},
                {'tile_y': {"$lt":result[2]}},
                {'tile_y': {"$gt":result[3]}},
                {'b': {'$gte': minR*0.3}}  # a good number to use, objects smaller than this size is hard to display

            ]
        },

            {
            '_id':0,
            'loc':0
        })

        return cursor

    # remeber to exclude the meta document
    @gen.coroutine
    def getVoronoi(self, collection):
        """Retriev the entire catalog.

        The retured catalog will be used to calculate Voronoi diagram at the front-end.

        Args:
            collection(str): Collection name for the required catalog.

        Returns:
            A cursor object with the required data.
        """
        coll = self.db[collection]
        cursor = coll.find({'_id':{'$ne':'meta'}}, {
            '_id': 0,
            'RA': 1,
            'DEC': 1,
        })
        return cursor

    def getCoordRange(self, xc, yc, zoom, maxZoom):
        """Determine the projection of a tile on the maximum zoom level.

        For tiles at lower (smaller) zoom levels, this function returns tile coordinates for the set of tiles that cover the same area as the provided one at the maximum zoom level.

        Args:
            xc(int): x-coordinate of the required tile.
            yc(int): y-coordinate of the required tile.
            zoom(int): Zoom level of the required tile.
            maxZoom(int): Maximum allowed zoom for the particular catalog
                collection.
        Returns:
            A tuple representing the smallest and largest coordinate in both x and y direction.

        """
        multi = 2**(int(maxZoom)-int(zoom))
        xMin = int(xc)*multi - 1
        xMax = (int(xc)+1)*multi
        yMin = int(yc)*multi - 1
        yMax = (int(yc)+1)*multi

        return (xMax, xMin, yMax, yMin)

    def getMinRadius(self, zoom, mapSizeV):
        """Returns the length scale of a one pixel.

        Converting from pixel to degree, with provided projecting zoom level and the size of the map measure in degree.

        Args:
            zoom(int): The projected zoom level.
            mapSizeV(float): The size of the map in vertial direction.

        Returns:
            float: A length correspoding to one pixel given the zoom level
                and map szie.
        """
        return float(mapSizeV)/(256*(2**(int(zoom))))

    @gen.coroutine
    def getMst(self, coll):
        """Retrive previously calcuated minimum spanning tree (MST).

        Args:
            coll(str): Associated catalog collection name for the
                requested MST.

        Returns:
            A cursor object
        """
        cusor_m = self.db['mst'].find({'_id': coll}, {'_id': 0, 'tree': 1})
        return cusor_m

    @gen.coroutine
    def getHealpix(self, coll):
        """Retrive previously calcuated Healpix grid.

        Args:
            coll(str): Associated catalog collection name for the
                requested Healpix grid.
        Returns:
            A cursor object
        """
        cursor_h = self.db['healpix'].find({'_id':coll}, {'_id':0, 'data':1})
        return cursor_h

    @gen.coroutine
    def getCircles(self, coll):
        """Retrive previously imported circles layer data.

        Args:
            coll(str): Associated catalog collection name for the
                requested circles layer.
        Returns:
            A cursor object
        """
        cursor_c = self.db['circles'].find({'_id':coll}, {'_id':0, 'data':1})
        return cursor_c

    def getOjbectByPos(self, coll, ra, dec):
        """Query the data for a particular object.

        Args:
            coll(str): The collection to search for object.
            ra(float): ``RA`` for the requested object.
            dec(float): ``DEC`` for the requested object.

        Returns:
            The data for the requested object stored in a dictionary.
        """
        # inputs from tornado are strings, need to convert
        ra = float(ra)
        dec = float(dec)
        pop_cursor = self.stat_db[coll].find({
            '$and':[{'RA':ra},{'DEC':dec}]},
            {'_id': 0, 'tile_x': 0, 'tile_y': 0, 'a': 0, 'b': 0, 'loc':0, 'theta':0}
        )
        return dumps(pop_cursor)

    def getRectSelection(self, coll, swLng, swLat, neLng, neLat):
        """Query data requested using selction tool.

        Args:
            coll(str): The collection to search for data.
            swLng(float): The longitude of the southwest corner on the
                selection bound.
            swLat(float): The latitute of the southwest corner on the
                selection bound.
            neLng(float): The longitude of the northeast corner on the
                selection bound.
            neLat(float): The latitute of the northeast corner on the
                selection bound.

        Returns:
            A list of dictionary for the returned catalog.
        """
        swLat = float(swLat)
        swLng = float(swLng)
        neLat = float(neLat)
        neLng = float(neLng)
        minR = self.getMinRadius(self.zoom_dict[coll], self.range_dict[coll])
        cursor = self.stat_db[coll].find({'$and':[
            {
                'loc': {
                    '$geoWithin':{
                        '$box': [
                            [swLng,swLat],
                            [neLng,neLat]
                        ]
                    }
                }
            },
            {'b': {'$gte': minR*0.3}}
        ]},
            {'_id':0, 'tile_x': 0, 'tile_y': 0, 'a': 0, 'b': 0, 'loc':0, 'theta':0}
        )

        return list(cursor)
