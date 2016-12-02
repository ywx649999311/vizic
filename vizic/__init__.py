from ._version import version_info, __version__

from .astroleaflet import AstroMap, GridLayer
from .control_widgets import *
from .connection import Connection


def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'static',
        'dest': 'jupyter-vizic',
        'require': 'jupyter-vizic/extension'
    }]
