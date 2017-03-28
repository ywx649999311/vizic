********
Overview
********

Vizic is a Jupyter widget library, which is designed for visualizing and interacting with astronomical catalog data. Vizic works inside Jupyter notebook environment. Vizic can be adopted in variety of exercises, for example, data inspection, clustering analysis, galaxy alignment studies, outlier identification or just large-scale visualizations for large datasets.

============
Introduction
============

Vizic takes advantages of Jupyter HTML widgets and Leaflet to enable fast and efficient browse and visualization of large astronomical catalogs. Jupyter HTML widgets are a set of HTML elements that allows easy interaction with the script running by IPython kernels. At the front-end, `Leaflet` is a JavaScript library, well known for building interactive map application on the web.

The integration of `Leaflet` and Jupyter Notebook App is provided by `ipyleaflet`. Inspired by and based `ipyleaflet`, Vizic added a vectorized tile layer and a Jupyter sever extension to make interactive visualization of catalog data possible in Jupyter notebooks.

================
Rich Interaction
================

Beyond the basic browsing of visualized catalog data in a map like application, Vizic added rich features allowing users to filter or colormap displayed catalog by property values.

===============
Custom Overlays
===============

The most unique feature of Vizic is its capability to graphically display the hidden pattern revealed by the geospatial distribution of astronomical objects in given catalogs, for example large-scale structure. Vizic offers several graphical tools to achieve this goal, namely Voronoi overlay, Delaunay overlay, Minimum Spanning Tree overlay and Healpix Grid overlay. For any given visualized catalog in a tiled layer, overlays mentioned above can be generated using the dataset being visualized and appended on top of the catalog layer. Such overlays can also zoom and shift to accommodate the movement of the base tiled layer.

To enable fast search of large scale structures, appended minimum spanning tree can be trimmed by maximum edge length and minimum branch size.
