[![ascl:1701.002](https://img.shields.io/badge/ascl-1701.002-blue.svg?colorB=262255)](http://ascl.net/1701.002)

# Vizic

A Jupyter widget for visualizing astronomical catalog data

## Note

Part of the project was orginally forked from [ipyleaflet](https://github.com/ellisonbg/ipyleaflet), which is a Jupyter / Leaflet bridge enabling interactive maps in the Jupyter notebook. As a major component of Vizic, ipyleaflet has been modified and improved in a way to better suite the needs of Vizic.

## Dependencies:

```
MongoDB
```

## Installation

```
$ pip3 install vizic
$ jupyter nbextension enable --py --sys-prefix widgetsnbextension
$ jupyter nbextension enable --py --sys-prefix vizic
```

For a development installation (requires npm):

```
$ git clone https://github.com/ywx649999311/vizic.git
$ cd vizic
$ pip install -e .
$ jupyter nbextension install --py --symlink --sys-prefix vizic
$ jupyter nbextension enable --py --sys-prefix widgetsnbextension
$ jupyter nbextension enable --py --sys-prefix vizic
```

To run the Jupyter Notebook with:

```
$ jupyter notebook --NotebookApp.nbserver_extensions="{'vizic.mongo_ext.extension':True}"
```

Note for developers: the `--symlink` argument on Linux or OS X allows one to modify the JavaScript code in-place. This feature is not available with Windows.

## Documentation

For detailed description, please refer to the [Vizic documentation](http://www.wx-yu.com/vizic/index.html).

## Reference

A paper about Vizic can be accessed on [AriXiv](https://arxiv.org/abs/1701.01222)
