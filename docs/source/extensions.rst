**********
Extensions
**********

At the front-end, all maps and layers are controlled by **Leaflet** JavaScript library. Initially, **Leaflet** is designed to work with tiled web maps stored as many PNG images. To make the visualization customizable, **Vizic** creates vector tiles on the fly from catalogs stored in MongoDB database.

The data pipeline is composed of two modules: **db_connect** and **extension**.
The **db_connect** provides all of the functions that are used to access the catalogs stored in the database. The **extension** module contains custom server handlers, which listen to URL requests, call the functions in the **db_connect** module and return requested information.

In the future, any added functionality that requires the access to the database by URL, can takes advantage of existing database utility function and custom server handlers found below. In addition, users can write their own database functions and server handlers. 

Regarding how to write custom server handler for Jupyter Notebook App, an in-depth explanation can be found here_.

	.. _here: http://jupyter-notebook.readthedocs.io/en/latest/extending/handlers.html

The API for existing database functions and custom server handlers can be found under **Database Utils** and **Server Handlers** respectively.

Database Utils
--------------

.. automodule:: vizic.mongo_ext.db_connect

    .. autoclass:: MongoConnect
        :members:

Server Handlers
---------------

.. automodule:: vizic.mongo_ext.extension
    :members:
    :undoc-members:
    :show-inheritance:
