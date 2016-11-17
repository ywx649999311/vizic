from ipyastroleaflet.leaflet import *
from ipywidgets import *
from traitlets import Unicode, dlink, link, Dict, Undefined
import pymongo as pmg
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
import uuid
from notebook.utils import url_path_join
import requests
import json


class AstroMap(Map):

    @default('layout')
    def _default_layout(self):
        return Layout(height='512px', width='512px')
    inertia = Bool(False).tag(sync=True, o=True)
    scroll_wheel_zoom = Bool(True).tag(sync=True, o=True)
    wheel_debounce_time = Int(60).tag(sync=True, o=True)
    wheel_px_per_zoom_level = Int(60).tag(sync=True, o=True)
    zoom = Int(1).tag(sync=True, o=True)
    max_zoom = Int(12).tag(sync=True, o=True)
    position_control = Bool(True).tag(sync=True, o=True)
    fullscreen_control = Bool(True).tag(sync=True, o=True)
    fade_animation = Bool(True).tag(sync=True, o=True)
    _des_crs = List().tag(sync=True)
    pan_loc = List().tag(sync=True)
    selection = Bool(False).tag(sync=True)
    s_bounds = List(help='LatLngBounds for selection tool').tag(sync=True)
    # pan_ready = Bool(False).tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.default_tiles is not None:
            self.default_tiles._map = self
            self._des_crs = self.default_tiles._des_crs
            self.max_zoom = self.default_tiles.max_zoom
            if self.center == [0.0, 0.0]:
                self.center = self.default_tiles.center
            self.default_tiles.visible = True

    def add_layer(self, layer):
        if layer.model_id in self.layer_ids:
            raise LayerException('layer already on map: %r' % layer)
        layer._map = self
        if isinstance(layer, GridLayer):
            self._des_crs = layer._des_crs
            self.max_zoom = layer.max_zoom
            self.center = layer.center
        self.layers = tuple([l for l in self.layers] + [layer])
        layer.visible = True

    def remove_layer(self, layer):
        if layer.model_id not in self.layer_ids:
            raise LayerException('layer not on map: %r' % layer)
        # if isinstance(layer, GridLayer):
        #     self._des_crs = [0, 0, 1, 1]
        self.layers = tuple([l for l in self.layers if l.model_id != layer.model_id])
        layer.visible = False

    def clear_layers(self):
        self.layers = ()

    def center_map(self):
        center = []
        try:
            center.append(self._des_crs[1]-128*self._des_crs[3])
            center.append(self._des_crs[0]+128*self._des_crs[2])
            self.fly_to(center, 1)
        except:
            print('No base tiles added!')

    def fly_to(self, latlng, zoom):
        latlng.append(zoom)
        self.pan_loc = latlng
        self.pan_loc = []


class GridLayer(RasterLayer):
    _view_name = Unicode('LeafletGridLayerView').tag(sync=True)
    _model_name = Unicode('LeafletGridLayerModel').tag(sync=True)

    bottom = Bool(False).tag(sync=True)
    _des_crs = List().tag(Sync=True)
    df = Instance(DataFrame, allow_none=True)
    min_zoom = Int(0).tag(sync=True, o=True)
    max_zoom = Int(8).tag(sync=True, o=True)
    # tile_size = Int(256).tag(sync=True, o=True)
    detect_retina = Bool(False).tag(sync=True, o=True)
    collection = Unicode().tag(sync=True, o=True)
    x_range = Float(1.0).tag(sync=True, o=True)
    y_range = Float(1.0).tag(sync=True, o=True)
    color = Unicode('red').tag(sync=True, o=True)
    # color object by property value
    custom_c = Bool(False).tag(sync=True)
    c_min_max = List().tag(sync=True)
    c_field = Unicode().tag(sync=True)
    # filter by property range
    filter_obj = Bool(False, help="Fileter object by property value range").tag(sync=True)
    filter_property = Unicode(help="The proerty field used to sort objects").tag(sync=True)
    filter_range = List().tag(sync=True)
    center = List().tag(sync=True)
    obj_catalog = Instance(Series, allow_none=True)
    __minMax = {}
    _popup_callbacks = Instance(CallbackDispatcher, ())

    @observe('custom_c')
    def _update_color_src(self, change):
        if change['new'] is True and self.c_field in self.get_fields():
            self.c_min_max = self.__minMax[self.c_field]
        else:
            self.c_min_max = []

    @observe('c_field')
    def _update_c_min_max(self, change):
        if self.custom_c is True and self.c_field in self.get_fields():
            self.c_min_max = self.__minMax[change['new']]

    @observe('filter_obj')
    def _update_filter(self, change):
        if change['new'] is True and self.filter_property in self.get_fields():
            self.filter_range = self.__minMax[self.filter_property]
        elif change['new'] is False:
            self.filter_range = []
            # self.filter_property = ''

    @observe('filter_property')
    def __update_property(self, change):
        if self.filter_obj is True and self.filter_property in self.get_fields():
            self.filter_range = self.__minMax[change['new']]
        elif self.filter_property not in self.get_fields():
            self.filter_property = ''

    def __init__(self, connection, coll_name=None, **kwargs):
        super().__init__(**kwargs)
        try:
            self.db = connection.db
        except:
            raise Exception('Mongodb connection error! Check connection object!')

        self.coll_name = coll_name
        self._server_url = connection._url
        self._checkInput()
        self.push_data(self._server_url)
        self._popup_callbacks.register_callback(self._query_obj, remove=False)
        self.on_msg(self._handle_leaflet_event)

        print('Mongodb collection name is {}'.format(self.collection))

    def _checkInput(self):
        if not self.collection == '':
            meta = self.db[self.collection].find_one({'_id': 'meta'})
            self._des_crs = meta['adjust']
            self.x_range = meta['xRange']
            self.y_range = meta['yRange']
            self.__minMax = meta['minmax']
            self.db_maxZoom = int(meta['maxZoom'])
            if self.max_zoom > int(meta['maxZoom']):
                self.max_zoom = int(meta['maxZoom'])
        elif self.df is not None:
            clms = [x.upper() for x in list(self.df.columns)]

            if not set(['RA', 'DEC']).issubset(set(clms)):
                raise Exception("RA, DEC is required for visualization!")
            if not set(['A_IMAGE', 'B_IMAGE', 'THETA_IMAGE']).issubset(set(clms)):
                print('Without data for the object shape, every object will appear as a point')

            df_r, self._des_crs = self._data_prep(self.max_zoom, self.df)
            self.x_range = self._des_crs[2]*256
            self.y_range = self._des_crs[3]*256
            self._insert_data(df_r)
        else:
            raise Exception('Need to provide a collection name or a pandas dataframe!')

    def _data_prep(self, zoom, df):
        dff = df.copy()
        dff.columns = [x.upper() for x in dff.columns]
        (xMax, xMin) = (dff['RA'].max(), dff['RA'].min())
        (yMax, yMin) = (dff['DEC'].max(), dff['DEC'].min())
        scaleMax = 2**int(zoom)
        x_range = xMax - xMin
        y_range = yMax - yMin

        # find field min and max
        for col in self.df.columns:
            if df[col].dtype.kind == 'f':
                self.__minMax[col] = [df[col].min(), df[col].max()]

        dff['tile_x'] = ((dff.RA-xMin)*scaleMax/x_range).apply(np.floor).astype(int)
        dff['tile_y'] = ((yMax-dff.DEC)*scaleMax/y_range).apply(np.floor).astype(int)
        dff.loc[:, 'a'] = dff.loc[:, 'A_IMAGE'].apply(lambda x: x*0.267/3600)
        dff.loc[:, 'b'] = dff.loc[:, 'B_IMAGE'].apply(lambda x: x*0.267/3600)
        dff['ra'] = dff['RA']
        dff['dec'] = dff['DEC']
        # dff['zoom'] = int(zoom)

        xScale = x_range/256
        yScale = y_range/256
        return dff, [xMin, yMax, xScale, yScale]

    def _insert_data(self, df):
        if self.coll_name is not None:
            self.collection = self.coll_name
        if self.collection == '':
            coll_id = str(uuid.uuid4())
            self.collection = coll_id

        data_d = df.to_dict(orient='records')
        coll = self.db[self.collection]
        coll.insert_many(data_d, ordered=False)
        coll.insert_one({'_id': 'meta', 'adjust': self._des_crs, 'xRange': self.x_range, 'yRange': self.y_range, 'minmax': self.__minMax, 'maxZoom':self.max_zoom})
        bulk = coll.initialize_unordered_bulk_op()
        bulk.find({'_id':{'$ne':'meta'}}).update({'$rename':{'ra':'loc.lng'}})
        bulk.find({'_id':{'$ne':'meta'}}).update({'$rename':{'dec':'loc.lat'}})
        try:
            result = bulk.execute()
        except:
            print(result)
        coll.create_index([('loc', pmg.GEO2D)], name='geo_loc_2d', min=-90, max=360)
        coll.create_index([('RA', pmg.ASCENDING),('DEC', pmg.ASCENDING)], name='ra_dec')
        coll.create_index([('tile_x', pmg.ASCENDING),('tile_y', pmg.ASCENDING)], name='tile_x_y')

    def push_data(self, url):
        # The center is required, don't remove
        self.center = [self._des_crs[1]-self.y_range/2, self._des_crs[0]+self.x_range/2]
        mRange = (self.x_range + self.y_range)/2
        body = {
            'collection': self.collection,
            'mrange': mRange,
            'maxzoom': self.db_maxZoom
        }
        push_url = url_path_join(url, '/rangeinfo/')
        req = requests.post(push_url, data=body)

    def _handle_leaflet_event(self, _, content, buffers):
        if content.get('event', '') == 'popup: click':
            self._popup_callbacks(**content)

    def _query_obj(self, **kwargs):
        body = {'coll': self.collection,'RA': kwargs['RA'], 'DEC': kwargs['DEC']}
        popup_url = url_path_join(self._server_url, '/objectPop/')
        result = requests.get(popup_url, data=body)
        pop_dict = json.loads(result.text[1:-1])
        self.obj_catalog = Series(pop_dict)

    def get_fields(self):
        return self.__minMax.keys()

    def get_min_max(self, field):
        field = field.upper()
        if field in list(self.get_fields()):
            return self.__minMax[field]
        else:
            raise Exception('Error: column name provided not in database!')

    def _query_selection(self):
        selection_url = url_path_join(self._server_url, '/selection/')
        if self._map.s_bounds != []:
            bounds = self._map.s_bounds
            body = {
                'coll': self.collection,
                'swlng': bounds[0],
                'swlat': bounds[2],
                'nelng': bounds[1],
                'nelat': bounds[3],
            }
            res = requests.get(selection_url, data=body)
            selection_dict = json.loads(res.text)
            self.select_data = DataFrame(selection_dict)
        else:
            print('bounds for selection is empty')


class MstLayer(Layer):
    _view_name = Unicode('LeafletMstLayerView').tag(sync=True)
    _model_name = Unicode('LeafletMstLayerModel').tag(sync=True)
    mst_url = Unicode().tag(sync=True)
    # cut_tree = Bool(False).tag(sync=True)
    max_len = Float(0.0).tag(sync=True)
    visible = Bool(False).tag(sync=True)

    def __init__(self, connection, collection, **kwargs):
        super().__init__(**kwargs)
        try:
            self.db = connection.db
        except:
            raise Exception('Mongodb connection error! Check connection object!')
        self._server_url = connection._url
        self.mst_url = url_path_join(self._server_url, '/mst/{}.json'.format(collection))

    def cut(self, length):
        self.max_len = float(length)

    def recover(self):
        self.max_len = 0.0
