*********
Vizic API
*********


Connection
----------

.. automodule:: vizic.connection
    :members:

Map & Layers
------------

.. automodule:: vizic.astroleaflet

    .. autoclass:: AstroMap
        :members:
    .. autoclass:: GridLayer
        :members:

    Custom overlays
    ^^^^^^^^^^^^^^^
    .. autoclass:: VoronoiLayer
        :members:
    .. autoclass:: DelaunayLayer
        :members:
    .. autoclass:: HealpixLayer
        :members:
    .. autoclass:: CirclesOverLay
        :members:
    .. autoclass:: MstLayer
        :members:

Control Widgets
---------------

Classes in this modules are used to create widgets to interact with visualized catalogs.

.. automodule:: vizic.control_widgets
    :members:

Utils
-----

The following functions are responsible for generating and modifying Minimum Spanning Tree and HEALPix Grids from a given dataset.

.. automodule:: vizic.utils
    :members:
