ipydesleaflet
==========

A Jupyter widget for visualizing astronomical catalog data

Note
----

Part of the project was orginally forked from [ipyleaflet](https://github.com/ellisonbg/ipyleaflet), which is a Jupyter / Leaflet bridge enabling interactive maps in the Jupyter notebook. As a major component of ipydesleaflet, ipyleaflet has been modified and improved in a way to better support the needs of ipydesleaflet. 

Installation
------------

Using pip:

```
$ pip install ipydesleaflet
$ jupyter nbextension enable --py --sys-prefix ipydesleaflet
```

For a development installation (requires npm):

```
$ git clone https://github.com/ellisonbg/ipydesleaflet.git
$ cd ipydesleaflet
$ pip install -e .
$ jupyter nbextension install --py --symlink --sys-prefix ipydesleaflet
$ jupyter nbextension enable --py --sys-prefix ipydesleaflet
```

Note for developers: the `--symlink` argument on Linux or OS X allows one to
modify the JavaScript code in-place. This feature is not available
with Windows.


