from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler
# from . import db_util as du
from .db_connect import MongoConnect
from tornado import gen
import json
import tornado.web

connection = None


class tileHandler(IPythonHandler):

    @gen.coroutine
    def get(self, coll, zoom, xc, yc):
        global connection
        if connection is None:
            self.set_status(403)
            self.write({'msg': 'error'})
        else:
            tile_gen = yield connection.getTileData(coll, xc, yc, zoom)
            tile_list = yield tile_gen.to_list(length=100000000)
            tile_json = json.dumps(tile_list)
            self.set_status(200)
            self.set_header('Content-Type', 'application/json')
            self.write(tile_json)


class dbHandler(IPythonHandler):

    @tornado.web.asynchronous
    def post(self):
        '''REST API to change mongodb connection.

        '''
        arguments = {k.lower(): self.get_argument(k) for k in self.request.arguments}
        host = arguments['host']
        port = int(arguments['port'])
        db = arguments['db']
        global connection

        if connection is not None:
            connection.close()
        try:
            connection = MongoConnect(host, port, db)
        except Exception as e:
            self.set_status(403)
            self.write({'status': 'error', 'message': 'check connection info'})
            raise Exception(str(e))
        else:
            self.set_status(200)
            self.write({'status': 'ok'})

        self.flush()
        self.finish()


class rangeHandler(IPythonHandler):

    def post(self):
        '''API to push range data to adictionary

        '''
        arguments = {k.lower(): self.get_argument(k) for k in self.request.arguments}
        collection = arguments['collection']
        mRange = arguments['mrange']
        maxZoom = arguments['maxzoom']
        MongoConnect.range_dict[collection] = float(mRange)
        MongoConnect.zoom_dict[collection] = int(maxZoom)


class popupHandler(IPythonHandler):
    '''API to query catalog data for individual object

    '''

    def get(self):
        arguments = {k.lower(): self.get_argument(k) for k in self.request.arguments}
        coll = arguments['coll']
        ra = arguments['ra']
        dec = arguments['dec']
        content = connection.getOjbectByPos(coll, ra, dec)
        self.set_status(200)
        self.set_header('Content-Type', 'application/json')
        self.write(content)


class selectionHandler(IPythonHandler):
    '''API to query catalog data for a selection

    '''

    def get(self):
        arguments = {k.lower(): self.get_argument(k) for k in self.request.arguments}
        coll = arguments['coll']
        swLng = arguments['swlng']
        neLng = arguments['nelng']
        swLat = arguments['swlat']
        neLat = arguments['nelat']
        content = connection.getRectSelection(coll, swLng, swLat, neLng, neLat)
        json_str = json.dumps(content)
        self.set_status(200)
        self.set_header('Content-Type', 'application/json')
        self.write(json_str)


class mstHandler(IPythonHandler):
    '''Listening to request for mst data
    '''
    @gen.coroutine
    def get(self, coll):
        global connection
        if connection is None:
            self.set_status(403)
            self.write({'msg': 'error'})
        else:
            mst_gen = yield connection.getMst(coll)
            mst_list = yield mst_gen.to_list(length=1000000000)
            mst_json = json.dumps(mst_list[0]['tree'])
            self.set_status(200)
            self.set_header('Content-Type', 'application/json')
            self.write(mst_json)

        self.flush()
        self.finish()


class voronoiHandler(IPythonHandler):
    '''Listening to request for voronoi data
    '''
    @gen.coroutine
    def get(self, coll):
        global connection
        if connection is None:
            self.set_status(403)
            self.write({'msg': 'error'})
        else:
            voronoi_gen = yield connection.getVoronoi(coll)
            voronoi_list = yield voronoi_gen.to_list(length=1000000000)
            voronoi_json = json.dumps(voronoi_list)
            self.set_status(200)
            self.set_header('Content-Type', 'application/json')
            self.write(voronoi_json)

        self.flush()
        self.finish()


class healpixHandler(IPythonHandler):
    '''Listening to request for healpix data
    '''
    @gen.coroutine
    def get(self, coll):
        global connection
        if connection is None:
            self.set_status(403)
            self.write({'msg': 'error'})
        else:
            healpix_gen = yield connection.getHealpix(coll)
            healpix_list = yield healpix_gen.to_list(length=1000000000)
            healpix_json = json.dumps(healpix_list[0]['data'])
            self.set_status(200)
            self.set_header('Content-Type', 'application/json')
            self.write(healpix_json)

        self.flush()
        self.finish()


class circlesHandler(IPythonHandler):
    '''Listening to request for circles data
    '''
    @gen.coroutine
    def get(self, coll):
        global connection
        if connection is None:
            self.set_status(403)
            self.write({'msg': 'error'})
        else:
            circles_gen = yield connection.getCircles(coll)
            circles_list = yield circles_gen.to_list(length=1000000000)
            circles_json = json.dumps(circles_list[0]['data'])
            self.set_status(200)
            self.set_header('Content-Type', 'application/json')
            self.write(circles_json)

        self.flush()
        self.finish()


def load_jupyter_server_extension(nbapp):
    """
    nbapp is istance of Jupyter.notebook.notebookapp.NotebookApp
    nbapp.web_app is isntance of tornado.web.Application - can register new tornado.web.RequestHandlers
    to extend API backend.
    """
    nbapp.log.info('My Extension Loaded')
    web_app = nbapp.web_app
    host_pattern = '.*$'
    route_pattern = url_path_join(web_app.settings['base_url'], '/tiles/(\S*)/(-?[0-9]+)/(-?[0-9]+)/(-?[0-9]+).json')
    db_pattern = url_path_join(web_app.settings['base_url'], '/connection/?')
    collection_pattern = url_path_join(web_app.settings['base_url'], '/rangeinfo/?')
    popup_pattern = url_path_join(web_app.settings['base_url'], '/objectPop/?')
    selection_pattern = url_path_join(web_app.settings['base_url'], '/selection/?')
    mst_pattern = url_path_join(web_app.settings['base_url'], '/mst/(\S*).json')
    circles_pattern = url_path_join(web_app.settings['base_url'], '/circles/(\S*).json')
    healpix_pattern = url_path_join(web_app.settings['base_url'], '/healpix/(\S*).json')
    voronoi_pattern = url_path_join(web_app.settings['base_url'], '/voronoi/(\S*).json')
    web_app.add_handlers(host_pattern, [
        (route_pattern, tileHandler),
        (popup_pattern, popupHandler),
        (db_pattern, dbHandler),
        (collection_pattern, rangeHandler),
        (selection_pattern, selectionHandler),
        (mst_pattern, mstHandler),
        (circles_pattern, circlesHandler),
        (healpix_pattern, healpixHandler),
        (voronoi_pattern, voronoiHandler)
    ])
