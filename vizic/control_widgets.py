from .astroleaflet import *
from ipywidgets import *


class NotebookUrl(Widget):
    _view_name = Unicode('NotebookUrlView').tag(sync=True)
    _view_module = Unicode('jupyter-vizic').tag(sync=True)
    nb_url = Unicode().tag(sync=True)


class LayerColorPicker(ColorPicker):
    layer = Instance(Layer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.value = self.layer.color
        self.link(self.layer)
        if self.concise:
            self.width = '30px'

    def unlink(self):
        self.dlink.unlink()

    def link(self, layer):
        self.layer = layer
        self.dlink = dlink((self, 'value'), (self.layer, 'color'))


class PopupDis(Widget):
    """Popup display Widget"""
    _view_name = Unicode('PopupDisView').tag(sync=True)
    _view_module = Unicode('jupyter-vizic').tag(sync=True)
    _object_info = Dict().tag(sync=True)
    layer = Instance(GridLayer)
    data = Instance(Series, allow_none=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.layout.width = '100%'
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
    _view_module = Unicode('jupyter-vizic').tag(sync=True)
    _map = Instance(AstroMap, allow_none=True)

    def __init__(self, map, **kwargs):
        super().__init__(**kwargs)
        self._map = map
        self.layout = Layout(height='30px', width='30px')
        self.on_click(self.handle_click)

    def handle_click(self, b):
        if self._map is not None:
            self._map.center_map()


class CFDropdown(Dropdown):
    _active = Bool(False)

    def __init__(self, layer, **kwargs):
        super().__init__(**kwargs)
        self._layer = layer
        self.description = 'Property: '
        self.layout.width = '100%'
        self.options = list(self._layer.get_fields())
        dlink((self._layer,'custom_c'), (self, '_active'))

    def link(self):
        # either dlink or use @validate on python side instead
        self.link = dlink((self, 'value'), (self._layer, 'c_field'))

    def unlink(self):
        self.link.unlink()
        self._layer.c_field = ''
        del self.link

    @observe('_active')
    def update_active(self, change):
        if change['new'] is False:
            self.unlink()
        elif change['new'] is True:
            self.link()


class FilterSlider(FloatRangeSlider):
    readout_format = Unicode('.3f').tag(sync=True)

    def __init__(self, layer, field, **kwargs):
        super().__init__(**kwargs)
        self._layer = layer
        self.property = field.upper()
        self.min, self.max = (-1e6, 1e6)
        self.min, self.max = self._layer.get_min_max(field)
        self.value = [self.min, self.max]
        self.step = 0.0001
        self.layout.width = '100%'
        # self.link()

    def _change_field(self, field):
        self.property = field.upper()
        self.min, self.max = (-1e6, 1e6)
        self.min, self.max = self._layer.get_min_max(field)
        self.value = [self.min, self.max]

    def link(self):
        self._layer.filter_property = self.property
        self.link = dlink((self, 'value'), (self._layer, 'filter_range'))

    def unlink(self):
        self.link.unlink()
        del self.link
        self._layer.filter_property = ''


class FilterWidget(Box):
    filter_field = Unicode()
    _active = Bool(False)

    @default('layout')
    def _default_layout(self):
        return Layout(display='flex', flex_flow='column',align_items='stretch', width='100%')

    def __init__(self, layer, *pargs, **kwargs):
        super().__init__(*pargs, **kwargs)
        self._layer = layer
        self.dropDown = Dropdown(options=list(self._layer.get_fields()), width='100%')
        self.slider = FilterSlider(layer, self.dropDown.value)
        self.children = (self.dropDown, self.slider)
        dlink((self.dropDown, 'value'),(self, 'filter_field'))
        dlink((self._layer,'filter_obj'), (self, '_active'))

    def link(self):
        self.slider.link()

    def unlink(self):
        self.slider.unlink()

    @observe('filter_field')
    def update_field(self, change):
        if change['new'] != '':
            self._layer.filter_property = change['new']
            self.slider._change_field(change['new'])

    @observe('_active')
    def update_active(self, change):
        if change['new'] is False:
            self.unlink()


class FilterBox(Box):

    @default('layout')
    def _default_layout(self):
        return Layout(display='flex', align_items='stretch', justify_content='space_between')

    def __init__(self, layer, field, *pargs, **kwargs):
        super().__init__(*pargs, **kwargs)
        self.label = Label(field.upper())
        self.label.padding = '7px 2px 2px 2px'
        self.slider = FilterSlider(layer, field)
        self.children = (self.label, self.slider)

    def link(self):
        self.slider.link()

    def unlink(self):
        self.slider.unlink()


class SelectionTrig(ToggleButton):
    _view_name = Unicode('SelectionButtonView').tag(sync=True)
    _view_module = Unicode('jupyter-vizic').tag(sync=True)
    _map = Instance(AstroMap, allow_none=True)

    def __init__(self, map, **kwargs):
        super().__init__(**kwargs)
        self._map = map
        self.layout = Layout(height='30px', width='30px')

    def link(self):
        self.link = link((self, 'value'), (self._map, 'selection'))

    def unlink(self):
        self.link.unlink()
        del self.link


class GetDataButton(Button):
    '''Home button Widget'''
    _view_name = Unicode('GetDataButtonView').tag(sync=True)
    _view_module = Unicode('jupyter-vizic').tag(sync=True)
    _layer = Instance(GridLayer)

    def __init__(self, layer, **kwargs):
        super().__init__(**kwargs)
        self._layer = layer
        self.layout = Layout(height='30px', width='30px')
        self.on_click(self.handle_click)

    def handle_click(self, b):
        if self._layer._map is not None and self._layer._map.selection:
            self.disabled = True
            self._layer._query_selection()
            self.disabled = False
