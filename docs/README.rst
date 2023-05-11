eBlocBroker
===========

About
-----

eBlocBroker is a blockchain based autonomous computational resource broker.

Website: `http://ebloc.cmpe.boun.edu.tr <http://ebloc.cmpe.boun.edu.tr>`_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prerequisites
~~~~~~~~~~~~~

- `Slurm <https://github.com/SchedMD/slurm>`_,`Geth <https://geth.ethereum.org/docs/getting-started>`_,
  `IPFS <https://ipfs.io>`_,
  `prasmussen/gdrive <https://github.com/prasmussen/gdrive>`_,
  `owncloud/pyocclient <https://github.com/owncloud/pyocclient>`_,
  `eth-brownie <https://github.com/eth-brownie/brownie>`_,
  `ganache-cli <https://github.com/trufflesuite/ganache>`_

Using Docker
~~~~~~~~~~~~

You can use a sandbox container provided in the `./docker-compose.yml <./docker-compose.yml>`_ file for testing inside a Docker
environment.

This container provides everything you need to test using a Python 3.7 interpreter.

Start the test environment:

.. code:: bash

    docker build -t ebb:latest . --progress plain
    docker-compose up -d

To enter the shell of the running container in interactive mode, run:

.. code:: bash

    docker exec -it ebloc-broker_slurm_1 /bin/bash

To stop the cluster container, run:

.. code:: bash

    docker-compose down

Cloud Storages
~~~~~~~~~~~~~~

EUDAT
^^^^^

Create B2ACCESS user account and login into B2DROP:
:::::::::::::::::::::::::::::::::::::::::::::::::::

First, from `B2ACCESS home page <https://b2access.eudat.eu/home/>`_

``No account? Signup`` => ``Create B2ACCESS user account (username) only``

- `B2DROP login site <https://b2drop.eudat.eu/>`_

1.4.1.2 Create app password
:::::::::::::::::::::::::::

``Settings`` => ``Security`` => ``Create new app password`` and save it.

1.5 How to install required packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We have a helper script, which you can use to install all required external dependencies:

.. code:: bash

    source ./scripts/setup.sh

Next, type ``eblocbroker --help`` for basic usage information.

1.6 Requester
~~~~~~~~~~~~~

1.6.1 Submit Job
^^^^^^^^^^^^^^^^

In order to submit your job each user should already registered into eBlocBroker.
You can use `./broker/eblocbroker/register_requester.py <./broker/eblocbroker/register_requester.py>`_ to register.
Please update following arguments inside ``register.yaml``.

After registration is done, each user should authenticate their ORCID iD using the following `http://eblocbroker.duckdns.org/ <http://eblocbroker.duckdns.org/>`_.

``$ ./eblocbroker.py submit job.yaml``

1.6.1.1 Example yaml file in order to define a job to submit.
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

``job.yaml``:

.. code:: yaml

    config:
        provider_address: '0x3e6ffc5ede9ee6d782303b2dc5f13afeee277aea'
        source_code:
    	cache_type: public
    	path: ~/test_eblocbroker/source_code
    	storage_hours: 0
    	storage_id: ipfs
        base_data_path: ~/test_eblocbroker/test_data/base/
        data:
    	data1:
    	    cache_type: public
    	    path: ~/test_eblocbroker/dataset_zip/small/KZ2-tsukuba
    	    storage_hours: 1
    	    storage_id: ipfs
    	data2:
    	    cache_type: public
    	    path: ~/test_eblocbroker/test_data/base/data/data1
    	    storage_hours: 0
    	    storage_id: ipfs
    	data3:
    	    hash: f13d75bc60898f0823566347e380a34b
        data_transfer_out: 1
        jobs:
    	job1:
    	    cores: 1
    	    run_time: 1

- ``path`` should represented as full path of the corresponding folder.

- ``cache_type`` should be variable from [ ``public``, ``private`` ]

- ``storaage_id`` should be variable from [ ``ipfs``, ``ipfs_gpg``, ``none``, ``eudat``, ``gdrive`` ]


------------

1.7 Provider
~~~~~~~~~~~~

Provider should run: `./eblocbroker.py <./eblocbroker.py>`_ driver Python script.

``$ ./eblocbroker.py driver``

1.7.1 Screenshot of provider GUI:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: /gui1.png
