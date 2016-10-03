from ._version import version_info, __version__

from .ipyatroleaflet import *

def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'static',
        'dest': 'jupyter-astro-leaflet',
        'require': 'jupyter-astro-leaflet/extension'
    }]
