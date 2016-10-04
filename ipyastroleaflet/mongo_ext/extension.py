from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler
from . import db_util as du
from tornado import gen
import json

class tileHandler(IPythonHandler):

    @gen.coroutine
    def get(self, zoom, xc, yc):
        # start = time.time()
        # print ('start', start)
        tile_gen = yield du.getTileData(xc, yc, zoom)
        tile_list = yield tile_gen.to_list(length = 100000000)
        tile_json = json.dumps(tile_list)
        # end = time.time()
        # print('end', end, time.time()-start)
        self.set_status(200)
        self.set_header('Content-Type', 'application/json')
        self.write(tile_json)

def load_jupyter_server_extension(nbapp):
    """
    nbapp is istance of Jupyter.notebook.notebookapp.NotebookApp
    nbapp.web_app is isntance of tornado.web.Application - can register new tornado.web.RequestHandlers
    to extend API backend.
    """
    nbapp.log.info('My Extension Loaded')
    web_app = nbapp.web_app
    host_pattern = '.*$'
    route_pattern = url_path_join(web_app.settings['base_url'], '/tiles/(-?[0-9]+)/(-?[0-9]+)/(-?[0-9]+).json')
    web_app.add_handlers(host_pattern, [(route_pattern, tileHandler)])
