**********
Extensions
**********

The communication between the front-end Leaflet maps and the MongoDB database is empowered by custom server handlers. Leaflet maps at the front-end request data by URL. The associated server handlers query the database and returns data.

To further take advantages of the unique design provided by Vizic, users can add their own server handlers and enable additional features that require access to the database. Under **vizic.mongo_ext** subpackage, **extension** module hosts custom handlers and **db_connect** module has all the functions to query the database.

Regarding how to write custom server handler for Jupyter App, an in-depth explanation can be found here_.

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
