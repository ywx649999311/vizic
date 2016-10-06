#database util library for des data
import motor
from tornado import gen
import concurrent.futures as cfs
import time

# coll = db['des']
# mst_coll = db['mst']

# executor = cfs.ThreadPoolExecutor(max_workers=20)
class MongoConnect:

	def __init__(self, host, port, db, coll='des'):
		self.client = motor.motor_tornado.MotorClient(host, port)
		self.db = self.client[db]
		self.coll = self.db[coll]

	def close(self):
		self.client.close()

	@gen.coroutine
	def getTileData(self, xc, yc, zoom):
		# multiThread is not stable
		# result = executor.submit(getCoordRange, xc, yc, zoom).result()
		# minR = executor.submit(getMinRadius,zoom, 0.714).result()

		result = self.getCoordRange(xc, yc, zoom)
		minR = self.getMinRadius(zoom, 0.714)
		cursor = self.coll.find({

			'$and': [
				{'tile_x': {"$lt":result[0]}},
				{'tile_x': {"$gt":result[1]}},
				{'tile_y': {"$lt":result[2]}},
				{'tile_y': {"$gt":result[3]}},
				{'b': {'$gte': minR*0.3}} #a good number to use, objects smaller than this size is hard to display

			]
		},

		{
			'RA':1,
			'DEC':1,
			'THETA_IMAGE':1,
			'COADD_OBJECTS_ID':1,
			'a':1,
			'b':1,
			'_id':0

		})

		#print ('query', time.time())
		return cursor

	@gen.coroutine
	def getVoronoi(self, tile):

		coll_v = db[tile]

		cursor_v = coll_v.find({},{

			'_id': 0,
			'RA': 1,
			'DEC': 1,
			})


		return cursor_v


	def getCoordRange(self, xc, yc, zoom):
		#print (8-int(zoom))
		multi = 2**(8-int(zoom))
		xMin = int(xc)*multi - 1
		xMax = (int(xc)+1)*multi
		yMin = int(yc)*multi -1
		yMax = (int(yc)+1)*multi



		return (xMax, xMin, yMax, yMin)

		#return result

	def getMinRadius(self, zoom, mapSizeV):

		return float(mapSizeV)/(256*(2**(int(zoom))))

	@gen.coroutine
	def getMst(self, tile):
		cusor_m = mst_coll.find({'tile_id': tile}, {'_id': 0, 'tree':1})

		return cusor_m
