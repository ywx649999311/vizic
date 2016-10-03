from ipyastroleaflet.leaflet import *

class AstroMap(Map):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clear_layers()
