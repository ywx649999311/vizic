# database util library for des data
import motor
from tornado import gen
import concurrent.futures as cfs
import time
from pymongo import MongoClient
from bson.json_util import dumps
# executor = cfs.ThreadPoolExecutor(max_workers=20)


class MongoConnect(object):

    range_dict = {}
    zoom_dict = {}

    def __init__(self, host, port, db):
        self.client = motor.motor_tornado.MotorClient(host, port)
        self.db = self.client[db]
        self.stat_client = MongoClient(host, port)
        self.stat_db = self.stat_client[db]

    def close(self):
        self.client.close()
        self.stat_client.close()

    @gen.coroutine
    def getTileData(self, coll, xc, yc, zoom):
        # multiThread is not stable
        # result = executor.submit(getCoordRange, xc, yc, zoom).result()
        # minR = executor.submit(getMinRadius,zoom, 0.714).result()
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

        # print ('query', time.time())
        return cursor

    # remeber to exclude the meta document
    @gen.coroutine
    def getVoronoi(self, collection):
        coll = self.db[collection]
        cursor = coll.find({'_id':{'$ne':'meta'}}, {
            '_id': 0,
            'RA': 1,
            'DEC': 1,
        })
        return cursor

    def getCoordRange(self, xc, yc, zoom, maxZoom):
        multi = 2**(int(maxZoom)-int(zoom))
        xMin = int(xc)*multi - 1
        xMax = (int(xc)+1)*multi
        yMin = int(yc)*multi - 1
        yMax = (int(yc)+1)*multi

        return (xMax, xMin, yMax, yMin)

    def getMinRadius(self, zoom, mapSizeV):

        return float(mapSizeV)/(256*(2**(int(zoom))))

    @gen.coroutine
    def getMst(self, coll):
        cusor_m = self.db['mst'].find({'_id': coll}, {'_id': 0, 'tree': 1})
        return cusor_m

    @gen.coroutine
    def getHealpix(self, coll):
        cursor_h = self.db['healpix'].find({'_id':coll}, {'_id':0, 'data':1})
        return cursor_h

    @gen.coroutine
    def getCircles(self, coll):
        cursor_c = self.db['circles'].find({'_id':coll}, {'_id':0, 'data':1})
        return cursor_c

    def getOjbectByPos(self, coll, ra, dec):
        # inputs from tornado are strings, need to convert
        ra = float(ra)
        dec = float(dec)
        pop_cursor = self.stat_db[coll].find({
            '$and':[{'RA':ra},{'DEC':dec}]},
            {'_id': 0, 'tile_x': 0, 'tile_y': 0, 'a': 0, 'b': 0, 'loc':0, 'theta':0}
        )
        return dumps(pop_cursor)

    def getRectSelection(self, coll, swLng, swLat, neLng, neLat):

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
