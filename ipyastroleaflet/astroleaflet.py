from ipyastroleaflet.leaflet import *
from ipywidgets import (
    Widget, Layout
)
from traitlets import Unicode

class AstroMap(Map):

    @default('layout')
    def _default_layout(self):
        return Layout(height='600px', width='600px')

    scroll_wheel_zoom = Bool(True).tag(sync=True, o=True)
    wheel_debounce_time = Int(80).tag(sync=True, o=True)
    wheel_px_per_zoom_level = Int(80).tag(sync=True, o=True)
    zoom = Int(1).tag(sync=True, o=True)
    max_zoom = Int(12).tag(sync=True, o=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clear_layers()

class NotebookUrl(Widget):
    _view_name = Unicode('NotebookUrlView').tag(sync=True)
    _view_module = Unicode('jupyter-astro-leaflet').tag(sync=True)
    nb_url = Unicode().tag(sync=True)

class GridLayer(RasterLayer):
    _view_name = Unicode('LeafletGridLayerView').tag(sync=True)
    _model_name = Unicode('LeafletGridLayerModel').tag(sync=True)

    bottom = Bool(False).tag(sync=True)
    # min_zoom = Int(0).tag(sync=True, o=True)
    # max_zoom = Int(18).tag(sync=True, o=True)
    # tile_size = Int(256).tag(sync=True, o=True)
    # xc = Int(3).tag(sync=True, o=True)
    # yc = Int(3).tag(sync=True, o=True)
    # detect_retina = Bool(False).tag(sync=True, o=True)
