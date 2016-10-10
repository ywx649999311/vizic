from ipyastroleaflet.leaflet import *
from ipywidgets import (
    Widget, Layout
)
from traitlets import Unicode
import pymongo

class AstroMap(Map):

    @default('layout')
    def _default_layout(self):
        return Layout(height='512px', width='512px')

    scroll_wheel_zoom = Bool(True).tag(sync=True, o=True)
    wheel_debounce_time = Int(60).tag(sync=True, o=True)
    wheel_px_per_zoom_level = Int(60).tag(sync=True, o=True)
    zoom = Int(1).tag(sync=True, o=True)
    max_zoom = Int(12).tag(sync=True, o=True)
    _des_crs = List().tag(sync=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clear_layers()

    def add_layer(self, layer):
        if layer.model_id in self.layer_ids:
            raise LayerException('layer already on map: %r' % layer)
        layer._map = self
        if isinstance(layer, GridLayer):
            self._des_crs = layer._des_crs
        self.layers = tuple([l for l in self.layers] + [layer])
        layer.visible = True

    def remove_layer(self, layer):
        if layer.model_id not in self.layer_ids:
            raise LayerException('layer not on map: %r' % layer)
        if isinstance(layer, GridLayer):
            self._des_crs = []
        self.layers = tuple([l for l in self.layers if l.model_id != layer.model_id])
        layer.visible = False
    def clear_layers(self):
        self.layers = ()
        self._des_crs = []
class NotebookUrl(Widget):
    _view_name = Unicode('NotebookUrlView').tag(sync=True)
    _view_module = Unicode('jupyter-astro-leaflet').tag(sync=True)
    nb_url = Unicode().tag(sync=True)

class GridLayer(RasterLayer):
    _view_name = Unicode('LeafletGridLayerView').tag(sync=True)
    _model_name = Unicode('LeafletGridLayerModel').tag(sync=True)

    bottom = Bool(False).tag(sync=True)
    _des_crs = List([322.477471,1.08749, 0.00278884, 0.0027886]).tag(Sync=True)
    # min_zoom = Int(0).tag(sync=True, o=True)
    # max_zoom = Int(18).tag(sync=True, o=True)
    # tile_size = Int(256).tag(sync=True, o=True)
    # detect_retina = Bool(False).tag(sync=True, o=True)

    def __init__(self, connection, collection = None, **kwargs):

        super().__init__(**kwargs)
        self.db = connection.db
        if collection is not None:
            _des_crs = self.db[collection].find_one({'_id':'meta'})['adjust']
