*******
Install
*******

Vizic uses MongoDB to ensure the best performance on data acquisition. So the first step is install MongoDB (at least the Python driver) on the machine where the Jupyter App is running.

For detailed instructions on the installation of MongoDB and associated tools, please refer to `here <https://docs.mongodb.com/manual/installation/>`_

**Install and enable Vizic**::

	pip3 install vizic
	jupyter nbextension enable --py --sys-prefix widgetsnbextension
	jupyter nbextension enable --py --sys-prefix vizic

**Development installation**::

	git clone https://github.com/ywx649999311/vizic.git
	cd vizic
	pip install -e .
	jupyter nbextension install --py --symlink --sys-prefix vizic
	jupyter nbextension enable --py --sys-prefix widgetsnbextension
	jupyter nbextension enable --py --sys-prefix vizic
