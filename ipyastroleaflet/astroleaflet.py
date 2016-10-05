from ipyastroleaflet.leaflet import *
from ipywidgets import Widget
from traitlets import Unicode

class AstroMap(Map):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clear_layers()

class NotebookUrl(Widget):
    _view_name = Unicode('NotebookUrlView').tag(sync=True)
    # _model_name = Unicode('NotebookUrlModel').tag(sync=True)
    _view_module = Unicode('jupyter-astro-leaflet').tag(sync=True)
    # _model_module = Unicode('jupyter-astro-leaflet').tag(sync=True)
    # options = List(trait=Unicode).tag(sync=True)
    nb_url = Unicode().tag(sync=True)
