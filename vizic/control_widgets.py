from .astroleaflet import *


class NotebookUrl(Widget):
    """Widget to get Jupyter server url.

    The actural url of the Jupyter server is assigned to class variable ``nb_url`` after the widget being rendered.
    """
    _view_name = Unicode('NotebookUrlView').tag(sync=True)
    _view_module = Unicode('jupyter-vizic').tag(sync=True)
    nb_url = Unicode().tag(sync=True)


class LayerColorPicker(ColorPicker):
    """Layer colorpicker widget.

    Attributes:
        layer: The layer of which the color is being controlled by the picker.

    """
    layer = Instance(Layer)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.value = self.layer.color
        self.link(self.layer)
        if self.concise:
            self.width = '30px'

    def unlink(self):
        """Unlink colorpicker and layer."""
        self.dlink.unlink()

    def link(self, layer):
        """Link the colorpicker to the layer.

        Used directional link from value attribute to the color attribute of the target layer object.
        """
        self.layer = layer
        self.dlink = dlink((self, 'value'), (self.layer, 'color'))


class PopupDis(Widget):
    """Popup display Widget

    Attributes:
        layer: The base tilelayer that the widget is monitoring.
    """
    _view_name = Unicode('PopupDisView').tag(sync=True)
    _view_module = Unicode('jupyter-vizic').tag(sync=True)
    _object_info = Dict().tag(sync=True)
    layer = Instance(GridLayer)
    data = Instance(pd.Series, allow_none=True)

    def __init__(self, **kwargs):
        """Initiate the widget object create a direction link

        The link is from the obj_catalog attribute of the layer object to the data attribute in this widget.
        """
        super().__init__(**kwargs)
        # self.layout.width = '100%'
        self.dlink = dlink((self.layer, 'obj_catalog'), (self, 'data'))

    @observe('data')
    def _update_data(self,change):
        """Observe changes in ``data`` and update at front-end."""
        old = change['old']
        new = change['new']

        if old is Undefined:
            return

        if new is not None and not new.equals(old):
            self._object_info = new.to_dict()


class HomeButton(Button):
    """Home button Widget

    Reset the map to initial zoom level and center.
    """
    _view_name = Unicode('HomeButtonView').tag(sync=True)
    _view_module = Unicode('jupyter-vizic').tag(sync=True)
    _map = Instance(AstroMap, allow_none=True)

    def __init__(self, map, **kwargs):
        """
        Args:
            map: An AstroMap object, which the widget is intended to control.
            **kwargs: Arbitrary keyward arguments for ``Button``.
        """
        super().__init__(**kwargs)
        self._map = map
        self.layout = Layout(height='30px', width='30px')
        self.on_click(self.handle_click)

    def handle_click(self, b):
        """Reset the map"""
        if self._map is not None:
            self._map.center_map()


class CFDropdown(Dropdown):
    """Dropdown menu for selecting colormapping field."""
    _active = Bool(False)

    def __init__(self, layer, **kwargs):
        """Extends ``Dropdown`` class from ``ipywidgets``.

        Args:
            layer: The tileLayer that the menu is associated with.
            **kwargs: Arbitrary keyward arguments for ``Dropdown``.
        """
        super().__init__(**kwargs)
        self._layer = layer
        self.description = 'Property: '
        self.layout.width = '100%'
        self.options = list(self._layer.get_fields())
        dlink((self._layer,'custom_c'), (self, '_active'))

    def link(self):
        """Link the value of the dropdown to ``c_field`` in tileLayer"""
        # either dlink or use @validate on python side instead
        self.link = dlink((self, 'value'), (self._layer, 'c_field'))

    def unlink(self):
        """Unlink for provided tileLayer"""
        self.link.unlink()
        self._layer.c_field = ''
        del self.link

    @observe('_active')
    def update_active(self, change):
        """Update the active status of the menu."""
        if change['new'] is False:
            self.unlink()
        elif change['new'] is True:
            self.link()


class ColorMap(Dropdown):
    """Dropdown menu for selecting colormapping color space."""
    _layer = Instance(GridLayer)
    colorSpaces = {
        'Spectral':1,
        'BrBG': 2,
        'PRGn': 3,
        'PiYG': 4,
        'PuOr': 5,
        'RdBu': 6,
        'RdYlBu':7,
        'RdYlGn':8,
        'Blues':9,
        'Greens':10,
        'Oranges':11,
        'Purples':12,
        'Reds':13,
        'BuGn':14,
        'BuPu':15,
        'GnBu':16,
        'OrRd':17,
        'PuBuGn':18,
        'PuBu':19,
        'PuRd':20,
        'RdPu':21,
        'YlGnBu':22,
        'YlGn':23,
        'YlOrBr':24,
        'YlOrRd':25
    }

    def __init__(self, gridlayer, **kwargs):
        """Extends ``Dropdown`` class from ``ipywidgets``.

        Args:
            gridlayer: The base tileLayer the widget is associate with.
            **kwargs: Arbitrary keyward arguments for ``Dropdown``.
        """
        super().__init__(**kwargs)
        self._layer = gridlayer
        self.description = 'ColorMap: '
        self.layout.width = '100%'
        self.options = self.colorSpaces
        self.value = self._layer.c_map
        dlink((self,'value'), (self._layer, 'c_map'))


class FilterSlider(FloatRangeSlider):
    """RangeSlider widget for filering displayed objects.

    Ranges for selected field are automatically displayed on the slider. Move the bars to filter out unwanted objects.

    Attributes:
        readout_format(str): The format of the float numbers, which show the
            value range of a particular property, on the slider.
    """
    readout_format = Unicode('.3f').tag(sync=True)

    def __init__(self, layer, field, **kwargs):
        """Extends ``FloatRangeSlider`` from ``ipywidgets``.

        Args:
            layer: A gridLayer instance.
            field(str): The property field of the catalog that the slider will
                use for filtering.
            **kwargs: Arbitrary keyword arguments for ``FloatRangeSlider``.
        """
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
        """Link slider values with the ``filter_range`` from tileLayer."""
        self._layer.filter_property = self.property
        self.link = dlink((self, 'value'), (self._layer, 'filter_range'))

    def unlink(self):
        """Unlink from the provided tileLayer."""
        self.link.unlink()
        del self.link
        self._layer.filter_property = ''


class FilterWidget(Box):
    """A Dropdown menu and a rangeSlider wrapped in a box layout.

    Select the field for filtering objects and perform the filter action in one widget. The map will reset when a new field is chosen.
    """
    filter_field = Unicode()
    _active = Bool(False)

    @default('layout')
    def _default_layout(self):
        return Layout(display='flex', flex_flow='column',align_items='stretch', width='100%')

    def __init__(self, layer, *pargs, **kwargs):
        """Extends ``Box`` from ``ipywidgets``.

        Two links are created: 1) link the dropDown menu with the ``filter_field`` attribute from the tileLayer. 2) link the ``filter_obj`` attribute from the tileLayer to the ``_active`` status attribute in this widget.
        Args:
            layer: A gridLayer instance.
            *args: Variable length argument list for ``Box``.
            **kwargs: Arbitrary keyword arguments for ``Box``.
        """
        super().__init__(*pargs, **kwargs)
        self._layer = layer
        self.dropDown = Dropdown(options=list(self._layer.get_fields()), width='100%')
        self.slider = FilterSlider(layer, self.dropDown.value)
        self.children = (self.dropDown, self.slider)
        dlink((self.dropDown, 'value'),(self, 'filter_field'))
        dlink((self._layer,'filter_obj'), (self, '_active'))

    def link(self):
        """Link the slider with the provided tileLayer."""
        self.slider.link()

    def unlink(self):
        """Unlink slider from the tileLayer."""
        self.slider.unlink()

    @observe('filter_field')
    def update_field(self, change):
        """Observe changes in the dropDown menu and updates"""
        if change['new'] != '':
            self._layer.filter_property = change['new']
            self.slider._change_field(change['new'])

    @observe('_active')
    def update_active(self, change):
        """Unlink this widget from layer if ``_active`` changes to False."""
        if change['new'] is False:
            self.unlink()


class FilterBox(Box):
    """A box layout wrapping a FilterSlider object."""
    @default('layout')
    def _default_layout(self):
        return Layout(display='flex', align_items='stretch', justify_content='space_between')

    def __init__(self, layer, field, *pargs, **kwargs):
        """Extends ``Box`` from ``ipywidgets``.

        Args:
            layer: A gridLayer instance.
            field(str): The property field of the catalog that the slider will
                use for filtering.
            *args: Variable length argument list for ``Box``.
            **kwargs: Arbitrary keyword arguments for ``Box``.
        """
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
    """A control widget to trigger lasso selection"""
    _view_name = Unicode('SelectionButtonView').tag(sync=True)
    _view_module = Unicode('jupyter-vizic').tag(sync=True)
    _map = Instance(AstroMap, allow_none=True)

    def __init__(self, map, **kwargs):
        """Extends ``ToggleButton`` from ``ipywidgets``.

        Args:
            map: An AstroMap map object that the trigger widget is associated
                with.
            **kwargs: Arbitray keyword arguments for ``ToggleButton``.
        """
        super().__init__(**kwargs)
        self._map = map
        self.layout = Layout(height='30px', width='30px')

    def link(self):
        """Link the trigger to target AstroMap object"""
        self.link = link((self, 'value'), (self._map, 'selection'))

    def unlink(self):
        """Unlink from the provided AstroMap"""
        self.link.unlink()
        del self.link


class GetDataButton(Button):
    """Getting selected data.

    Clicking this button to query the database for data selected using the lasso-like selection tool.
    """
    _view_name = Unicode('GetDataButtonView').tag(sync=True)
    _view_module = Unicode('jupyter-vizic').tag(sync=True)
    _layer = Instance(GridLayer)

    def __init__(self, layer, **kwargs):
        """Extends ``Button`` from ``ipywidgets``.

        Args:
            layer: The tileLayer that the button is asccoiate with.
        """
        super().__init__(**kwargs)
        self._layer = layer
        self.layout = Layout(height='30px', width='30px')
        self.on_click(self.handle_click)

    def handle_click(self, b):

        if self._layer._map is not None and self._layer._map.selection:
            self.disabled = True
            self._layer._query_selection()
            self.disabled = False
