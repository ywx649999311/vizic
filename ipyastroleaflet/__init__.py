from ._version import version_info, __version__

from .astroleaflet import AstroMap, GridLayer
from .app_widgets import *
from .connection import Connection


def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'static',
        'dest': 'jupyter-astro-leaflet',
        'require': 'jupyter-astro-leaflet/extension'
    }]
