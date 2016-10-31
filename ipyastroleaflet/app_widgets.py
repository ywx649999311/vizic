from .astroleaflet import *
from ipywidgets import *


class NotebookUrl(Widget):
    _view_name = Unicode('NotebookUrlView').tag(sync=True)
    _view_module = Unicode('jupyter-astro-leaflet').tag(sync=True)
    nb_url = Unicode().tag(sync=True)


class AstroColorPicker(ColorPicker):

    layer = Instance(GridLayer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.value = self.layer.color
        self.link(self.layer)
        if self.concise:
            self.width = '30px'

    def unlink(self):
        self.dlink.unlink()

    def link(self, g):
        self.layer = g
        self.dlink = dlink((self, 'value'), (self.layer, 'color'))


class PopupDis(Widget):
    """Popup display Widget"""
    _view_name = Unicode('PopupDisView').tag(sync=True)
    _view_module = Unicode('jupyter-astro-leaflet').tag(sync=True)
    _object_info = Dict().tag(sync=True)
    layer = Instance(GridLayer)
    data = Instance(Series, allow_none=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dlink = dlink((self.layer, 'obj_catalog'), (self, 'data'))

    @observe('data')
    def _update_data(self,change):
        old = change['old']
        new = change['new']

        if old is Undefined:
            return

        if new is not None and not new.equals(old):
            self._object_info = new.to_dict()


class HomeButton(Button):
    '''Home button Widget'''
    _view_name = Unicode('HomeButtonView').tag(sync=True)
    _view_module = Unicode('jupyter-astro-leaflet').tag(sync=True)
    _map = Instance(AstroMap, allow_none=True)

    def __init__(self, map, **kwargs):
        super().__init__(**kwargs)
        self._map = map
        self.layout = Layout(height='30px', width='30px')
        self.on_click(self.handle_click)

    def handle_click(self, b):
        if self._map is not None:
            self._map.center_map()
