from .astroleaflet import *
from .connection import Connection
from .control_widgets import *


def _jupyter_nbextension_paths():
    return [{
        'section': 'notebook',
        'src': 'static',
        'dest': 'jupyter-vizic',
        'require': 'jupyter-vizic/extension'
    }]
