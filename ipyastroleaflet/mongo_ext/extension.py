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
    web_app.add_handlers(host_pattern, [
        (route_pattern, tileHandler),
        (popup_pattern, popupHandler),
        (db_pattern, dbHandler),
        (collection_pattern, rangeHandler)
    ])
