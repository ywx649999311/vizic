ipyastroleaflet
==========

A Jupyter widget for visualizing astronomical catalog data

Note
----

Part of the project was orginally forked from [ipyleaflet](https://github.com/ellisonbg/ipyleaflet), which is a Jupyter / Leaflet bridge enabling interactive maps in the Jupyter notebook. As a major component of ipyastroleaflet, ipyleaflet has been modified and improved in a way to better suite the needs of ipyastroleaflet.

Dependencies:

    Node.js, npm
    MongoDB

Installation
------------
For a development installation (requires npm):

```
$ git clone https://github.com/ywx649999311/ipyastroleaflet.git
$ cd ipyastroleaflet
$ pip install -e .
$ jupyter nbextension install --py --symlink --sys-prefix ipyastroleaflet
$ jupyter nbextension enable --py --sys-prefix ipyastroleaflet
```

To run the Jupyter Notebook with:
```
$ jupyter notebook --NotebookApp.server_extensions="['ipyastroleaflet.mongo_ext.extension']"
```
Note for developers: the `--symlink` argument on Linux or OS X allows one to
modify the JavaScript code in-place. This feature is not available
with Windows.
