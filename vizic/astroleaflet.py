from .leaflet import *
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
from .healpix import get_vert_bbox
from .mst import *


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
    radius = Bool(False).tag(sync=True, o=True)
    point = Bool(False).tag(sync=True, o=True)
    df_rad = Int(2).tag(sync=True, o=True)
    scale_r = Float(1.0).tag(sync=True, o=True)

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
        elif self.custom_c is False:
            pass
        else:
            raise Exception('Color Field ({}) not valid!'.format(self.c_field))
            self.c_field = change['old']
        # return proposal['value']

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
            (self.radius,self.point) = (meta['radius'], meta['point'])
            self.db_maxZoom = int(meta['maxZoom'])
            if self.max_zoom > int(meta['maxZoom']):
                self.max_zoom = int(meta['maxZoom'])
        elif self.df is not None:
            clms = [x.upper() for x in list(self.df.columns)]
            exist_colls = self.db.collection_names()

            if not set(['RA', 'DEC']).issubset(set(clms)):
                raise Exception("RA, DEC is required for visualization!")
            if not set(['A_IMAGE', 'B_IMAGE', 'THETA_IMAGE']).issubset(set(clms)):
                print('No shape information provided')
                if 'RADIUS' in clms:
                    print('Will use radius for filtering!')
                    self.radius = True
                else:
                    print('Object as point, slow performance!')
                    self.point = True

            if self.coll_name is not None and self.coll_name in exist_colls:
                raise Exception('Collectoin name already exists, try to use a different name or remove the df argument.')
            df_r, self._des_crs = self._data_prep(self.max_zoom, self.df)
            self.x_range = self._des_crs[2]*256
            self.y_range = self._des_crs[3]*256
            self.db_maxZoom = self.max_zoom
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
        for col in dff.columns:
            if dff[col].dtype.kind == 'f':
                self.__minMax[col] = [dff[col].min(), dff[col].max()]

        dff['tile_x'] = ((dff.RA-xMin)*scaleMax/x_range).apply(np.floor).astype(int)
        dff['tile_y'] = ((yMax-dff.DEC)*scaleMax/y_range).apply(np.floor).astype(int)

        if self.radius:
            dff.loc[:, 'b'] = dff.loc[:, 'RADIUS'].apply(lambda x: x*0.267/3600)
            dff['theta'] = 0
        elif self.point:
            dff['b'] = 360
            dff['theta'] = 0
        else:
            dff.loc[:, 'a'] = dff.loc[:, 'A_IMAGE'].apply(lambda x: x*0.267/3600)
            dff.loc[:, 'b'] = dff.loc[:, 'B_IMAGE'].apply(lambda x: x*0.267/3600)
            dff.loc[:, 'theta'] = dff.loc[:, 'THETA_IMAGE']

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
        coll.insert_one({'_id': 'meta', 'adjust': self._des_crs, 'xRange': self.x_range, 'yRange': self.y_range, 'minmax': self.__minMax, 'maxZoom':self.max_zoom,'radius':self.radius,'point':self.point})
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
            raise Exception('Error: {} not in database!'.format(field))

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


class VoronoiLayer(Layer):
    _view_name = Unicode('LeafletVoronoiLayerView').tag(sync=True)
    _model_name = Unicode('LeafletVoronoiLayerModel').tag(sync=True)
    voronoi_url = Unicode().tag(sync=True)
    visible = Bool(False).tag(sync=True)
    color = Unicode('#88b21c').tag(sync=True, o=True)
    svg_zoom = Int(5).tag(sync=True, o=True)

    def __init__(self, gridLayer, **kwargs):
        super().__init__(**kwargs)
        try:
            self.db = gridLayer.db
        except:
            raise Exception('Mongodb connection error! Check connection object!')
        self._server_url = gridLayer._server_url
        self.voronoi_url = url_path_join(self._server_url, '/voronoi/{}.json'.format(gridLayer.collection))


class DelaunayLayer(Layer):
    _view_name = Unicode('LeafletDelaunayLayerView').tag(sync=True)
    _model_name = Unicode('LeafletDelaunayLayerModel').tag(sync=True)
    delaunay_url = Unicode().tag(sync=True)
    visible = Bool(False).tag(sync=True)
    color = Unicode('blue').tag(sync=True, o=True)
    svg_zoom = Int(5).tag(sync=True, o=True)

    def __init__(self, gridLayer, **kwargs):
        super().__init__(**kwargs)
        try:
            self.db = gridLayer.db
        except:
            raise Exception('Mongodb connection error! Check connection object!')
        self._server_url = gridLayer._server_url
        self.delaunay_url = url_path_join(self._server_url, '/voronoi/{}.json'.format(gridLayer.collection))


class HealpixLayer(Layer):
    _view_name = Unicode('LeafletHealpixLayerView').tag(sync=True)
    _model_name = Unicode('LeafletHealpixLayerModel').tag(sync=True)
    healpix_url = Unicode().tag(sync=True)
    visible = Bool(False).tag(sync=True)
    color = Unicode('white').tag(sync=True, o=True)
    svg_zoom = Int(5).tag(sync=True, o=True)
    nside = Int(1024)
    nest = Bool(True)

    def __init__(self, gridLayer, **kwargs):
        super().__init__(**kwargs)
        try:
            self.db = gridLayer.db
        except:
            raise Exception('Mongodb connection error! Check connection object!')
        # print(self.collection)
        if self.db['healpix'].find({'_id':gridLayer.collection}).count() < 1:
            self.inject_data(gridLayer)

        self._server_url = gridLayer._server_url
        self.healpix_url = url_path_join(self._server_url, '/healpix/{}.json'.format(gridLayer.collection))

    def inject_data(self, gridLayer):
        # [xmin, xmax, ymin, ymax]
        self.bbox = [gridLayer._des_crs[0],gridLayer._des_crs[1]-gridLayer.y_range, gridLayer._des_crs[0]+gridLayer.x_range, gridLayer._des_crs[1]]
        all_v = get_vert_bbox(self.bbox[0], self.bbox[1], self.bbox[2], self.bbox[3], self.nside, self.nest)
        polys = [{'ra':x[0].tolist(), 'dec': x[1].tolist()} for x in all_v]
        # inject data into mongodb
        self.db['healpix'].insert_one({'_id':gridLayer.collection, 'data':polys})


class CirclesOverLay(Layer):
    _view_name = Unicode('LeafletCirclesLayerView').tag(sync=True)
    _model_name = Unicode('LeafletCirclesLayerModel').tag(sync=True)
    circles_url = Unicode().tag(sync=True)
    visible = Bool(False).tag(sync=True)
    color = Unicode('purple').tag(sync=True, o=True)
    svg_zoom = Int(5).tag(sync=True, o=True)
    df = Instance(DataFrame, allow_none=True)
    radius = Int(50).tag(sync=True, o=True)
    cols = List(['RA', 'DEC'])

    def __init__(self, gridLayer, name, **kwargs):
        super().__init__(**kwargs)
        try:
            self.db = gridLayer.db
        except:
            raise Exception('Mongodb connection error! Check connection object!')
        self.document_id = name

        if self.db['circles'].find({'_id':name}).count() < 1:
            if self.df is None:
                raise Exception('Given overlay data id does not exist, a dataframe is required.')
            self.inject_data(name)

        self._server_url = gridLayer._server_url
        self.circles_url = url_path_join(self._server_url, '/circles/{}.json'.format(name))

    def inject_data(self, document_id):
        dff = self.df.copy()
        dff.columns = [x.upper() for x in dff.columns]
        cols = [x.upper() for x in self.cols]
        data = dff[cols].to_dict(orient='records')

        coll = self.db['circles']
        coll.insert_one({'_id':document_id, 'data':data})


class MstLayer(Layer):
    _view_name = Unicode('LeafletMstLayerView').tag(sync=True)
    _model_name = Unicode('LeafletMstLayerModel').tag(sync=True)
    mst_url = Unicode().tag(sync=True)
    # cut_tree = Bool(False).tag(sync=True)
    max_len = Float(0.0).tag(sync=True)
    visible = Bool(False).tag(sync=True)
    color = Unicode('#0459e2').tag(sync=True, o=True)
    svg_zoom = Int(5).tag(sync=True, o=True)
    line_idx = List().tag(sync=True)
    _cut_count = Int(0).tag(sync=True)

    def __init__(self, gridLayer, neighbors=15, **kwargs):
        super().__init__(**kwargs)
        try:
            self.db = gridLayer.db
        except:
            raise Exception('Mongodb connection error! Check connection object!')
        self.document_id = gridLayer.collection

        if self.db['mst'].find({'_id':self.document_id}).count() < 1:
            self.inject_data(neighbors)
        else:
            self.get_index()

        self._server_url = gridLayer._server_url
        self.mst_url = url_path_join(self._server_url, '/mst/{}.json'.format(self.document_id))

    def inject_data(self, neighbors):
        coll = self.db[self.document_id]
        cur_ls = list(coll.find({'_id':{'$ne':'meta'}},{'_id':0,'RA':1,'DEC':1}))
        df_pos = pd.DataFrame(cur_ls)
        m, index = get_mst(df_pos, neighbors)
        self.index = index
        mst_lines = m.to_dict(orient='records')
        self.db['mst'].insert_one({'_id':self.document_id, 'tree':mst_lines})

    def get_index(self):
        coll = self.db['mst']
        cur_ls = list(coll.find({'_id':self.document_id}))
        # lines_ls = cur_ls['tree']
        df_pos = pd.DataFrame(cur_ls[0]['tree'])
        self.index = get_m_index(df_pos)

    def cut(self, length, members):
        self.line_idx = cut_tree(self.index, length, members)
        self.max_len = float(length)
        self._cut_count += 1

    def recover(self):
        self.max_len = 0.0

    def get_data(self):
        coll = self.db['mst']
        cur_ls = list(coll.find({'_id':self.document_id}))
        return cur_ls[0]['tree']
