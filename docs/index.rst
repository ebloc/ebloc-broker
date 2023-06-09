https://github.com/ebloc/ebloc-broker/raw/dev/imgs/logo.png ebloc-broker
========================================================================

``eBlocBroker`` is a smart contract as an autonomous volunteer computing
and sharing data resource broker based on blockchain for e-Science. It
applies blockchain technology to provide a market for computational and
data resources to research communities.

For more info see:
`documentation <https://ebloc-broker-readthedocs.duckdns.org/>`__.

Prerequisites
-------------

-  `Slurm <https://github.com/SchedMD/slurm>`__,
   `IPFS <https://ipfs.io>`__,
   `eth-brownie <https://github.com/eth-brownie/brownie>`__,
   `prasmussen/gdrive <https://github.com/prasmussen/gdrive>`__,
   `owncloud/pyocclient <https://github.com/owncloud/pyocclient>`__,
   `ganache-cli <https://github.com/trufflesuite/ganache>`__.

Using Docker
------------

You can use a sandbox container provided in the
`./docker-compose.yml <./docker-compose.yml>`__ file for testing inside
a Docker environment.

This container provides everything you need to test using a
``Python 3.7`` interpreter. Start the test environment:

.. code:: bash

   docker-compose up -d

To enter the shell of the running container in the interactive mode,
run:

::

   docker exec --detach-keys="ctrl-e,e" -it ebloc-broker_slurm_1 /bin/bash

To stop the container, run:

.. code:: bash

   docker-compose down

Cloud Storages
--------------

B2DROP
~~~~~~

Create B2ACCESS user account and login into B2DROP:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, from `B2ACCESS home page <https://b2access.eudat.eu/home/>`__

``No account SignUp`` =>
``Create B2ACCESS user account (username) only``

-  `B2DROP login site <https://b2drop.eudat.eu/>`__

Create app password
^^^^^^^^^^^^^^^^^^^

``Settings`` => ``Security`` => ``Create new app password`` and save it.

How to install required packages
--------------------------------

We have a helper script, which you can use to install all required
external dependencies:

.. code:: bash

   source ./scripts/setup.sh

Next, type ``eblocbroker --help`` for basic usage information.

Requester
---------

Submit Job
~~~~~~~~~~

In order to submit your job each user should already registered into
eBlocBroker using
``eblocbroker register_provider ~/.ebloc-broker/cfg.yaml`` After
registration is done, each user should authenticate their ORCID iD using
the following http://eblocbroker.duckdns.org/.

.. code:: bash

   $ eblocbroker submit job.yaml

Example yaml file in order to define a job to submit.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``job.yaml`` :

.. code:: yaml

   config:
     requester_address: '0x378181ce7b07e8dd749c6f42772574441b20e35f'
     provider_address: '0x29e613b04125c16db3f3613563bfdd0ba24cb629'
     source_code:
       storage_id: ipfs
       cache_type: public
       path: ~/test_eblocbroker/run_cppr
       storage_hours: 0
     data:
       data1:
         hash: 4613abc322e8f2fdeae9a5dd10f17540
       data2:
         hash: 050e6cc8dd7e889bf7874689f1e1ead6
       data3:
         cache_type: public
         path: /home/alper/test_eblocbroker/small/BVZ-venus
         storage_hours: 1
         storage_id: ipfs
     data_transfer_out: 10
     jobs:
       job1:
         cores: 1
         run_time: 60

-  ``path`` should represented as full path of the corresponding folder.
-  ``cache_type`` should be variable from [ ``public``, ``private`` ]
-  ``storage_id`` should be variable from [ ``ipfs``, ``ipfs_gpg``,
   ``none``, ``b2drop``, ``gdrive`` ]

--------------

Provider
--------

Each provider should run ``eblocbroker driver`` for start running the
Python script.

.. image:: gui1.png

🎬 Demonstration
----------------

-  https://asciinema.org/a/551809
-  https://asciinema.org/a/551843

Acknowledgement
---------------

This work is supported by the Turkish Directorate of Strategy and Budget
under the TAM Project number 2007K12-873.

Developed by Alper Alimoglu and Can Ozturan from Bogazici University,
Istanbul. Contact alper.alimoglu@boun.edu.tr, ozturaca@boun.edu.tr if
necessary.
