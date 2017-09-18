************
Installation
************

Vizic uses MongoDB to ensure the best performance on data acquisition. So the first step is to install MongoDB on the machine where the Jupyter App is running or to have MongoDB installed on a remote location.

.. note::

	MongoDB 3.2 and above is recommended.

=======
MongoDB
=======

Installation instruction varies between different operation systems. Here we are using Ubuntu and OSX as examples. For detailed instructions on the installation of MongoDB and associated tools, please refer to `here <https://docs.mongodb.com/manual/installation/>`_

On Ubuntu 14.04
---------------

::

	# Import the public key used by the package management system.
	sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6
	# Create a list file for MongoDB.
	echo "deb [ arch=amd64 ] http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.4.list
	# Update package database and install MongoDB
	sudo apt-get update
	sudo apt-get install -y mongodb-org

On OSX
------

**Install with HomeBrew**::

	brew update
	brew install mongodb

.. note::

	To install MongoDB manually using binary files, please check out the instruction on MongoDB's `official page`_.

	.. _official page: https://docs.mongodb.com/manual/tutorial/install-mongodb-on-os-x/

=====
Vizic
=====

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
