***************
Getting Started
***************

Vizic uses MongoDB for data storage, and an added Jupyter server extension to direct catalog request to the database. Therefore the server extension also needed to be specified when starting the Jupyter App from the command line.

To start the App use::

	jupyter notebook --NotebookApp.nbserver_extensions="{'vizic.mongo_ext.extension':True}"

In addition, a running MongoDB instance is required. To start a new instance on the local machine, enter the following in a new terminal window::

	mongod

After the MongoDB database and the Jupyte App are setted up, we can start using Vizic. A few examples are provided in the github repo and also a test dataset.

	* `Basic Catalog Visualizations`_
	* `Selection Tool & Analysis`_
	* `Custom Overlays`_

	.. _Basic Catalog Visualizations: https://github.com/ywx649999311/vizic/blob/master/examples/demo1(basic).ipynb/
	.. _Selection Tool & Analysis: https://github.com/ywx649999311/vizic/blob/master/examples/demo2%20(selection%20tool%20%26%20analysis%20).ipynb
	.. _Custom Overlays: https://github.com/ywx649999311/vizic/blob/master/examples/demo3%20(custom%20overlays).ipynb
