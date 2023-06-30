Quickstart
==========

This page provides a quick overview of how to use ``ebloc-broker`` in
Docker container.

Creating a New Docker Container
-------------------------------

The first step to using ``ebloc-broker`` is to initialize a Docker
Container for the provider and requester. Start the test environment:

.. code:: bash

   # first run container for the provider
   cd ~/ebloc-broker
   docker-compose up -d --build --remove-orphans  # for the provider

   # then run the container for the requester
   cd docker/requester
   docker-compose up -d --build --remove-orphans

To enter the shell of the running container in the interactive mode, run
these in seperate terminals:

::

   docker exec --detach-keys="ctrl-e,e" -it ebloc-broker_slurm_1 /bin/bash
   docker exec --detach-keys="ctrl-e,e" -it requester_requester_1 /bin/bash

Provider
--------

First run one time:
``/workspace/ebloc-broker/broker/eblocbroker_scripts/update_provider_info.py``.
Example output:

.. code:: bash

   $ /workspace/ebloc-broker/broker/eblocbroker_scripts/update_provider_info.py
   ## address=0xe953A99FF799e6dA23948Ca876FCe3f264447De8
   ## gmail=
   ## ipfs_address=/ip4/85.96.2.179/tcp/4001/p2p/12D3KooWBvXo9ycG5BreJyLK5C9oDer9UVZX8VMMdAXS4usCrKvr
   ## fid=""
   Transaction sent: 0x6dad5e2461aec1f284ba899c6287f0f8f553c3d899011f335c3e2cf54c070048
     Gas price: 1.2 gwei   Gas limit: 9980000   Nonce: 168
     eBlocBroker.updateProviderInfo confirmed   Block: 21068055   Gas used: 30952 (0.31%)

   tx_hash=0x6dad5e2461aec1f284ba899c6287f0f8f553c3d899011f335c3e2cf54c070048
   tx={
   │   'blockHash': HexBytes('0x814d43942e49037f3f669db2986e9fe3060ac3804c6c91ea508f9b344e836f79'),
   │   'blockNumber': 21068055,
   │   'cumulativeGasUsed': 30952,
   │   'from': '0xe953A99FF799e6dA23948Ca876FCe3f264447De8',
   │   'gasUsed': 30952,
   │   'logs': [...],
   │   'status': 1,
   │   'to': '0x9C7570E55d6414561800D72045A72B26A5a9E639',
   │   'transactionHash': HexBytes('0x6dad5e2461aec1f284ba899c6287f0f8f553c3d899011f335c3e2cf54c070048'),
   │   'transactionIndex': 0
   }
   #> Is transaction successfully deployed?  [ok]

Followed by ``eblocbroker driver``.

.. code:: bash

   $ eblocbroker driver
   ================================================ provider session starts =================================================
   2023-07-01 11:34 -- is_threading=True -- pid=397 -- whoami=root -- slurm_user=slurm
   provider_address: 0xe953a99ff799e6da23948ca876fce3f264447de8
   rootdir: /workspace/ebloc-broker
   logfile: /root/.ebloc-broker/provider.log
   ipfs_id: /ip4/85.96.2.179/tcp/4001/p2p/12D3KooWBvXo9ycG5BreJyLK5C9oDer9UVZX8VMMdAXS4usCrKvr
   ipfs_repo_dir: /root/.ipfs
   Attached to host RPC client listening at 'http://berg-cmpe-boun.duckdns.org:8545'

   => is_web3_connected=True
   => active_network_id=bloxberg
   =>  left_of_block_number=20941981
   => latest_block_number=21068056
   🍺  Connected into bloxberg
   ## checking slurm...  [ok]
   ==> mongod is already running on the background
   ==> contract_address=0x9c7570e55d6414561800d72045a72b26a5a9e639
   ==> account_balance=91754976 gwei ≈ 0.09 ether
   ==> Ebb_token_balance=1999.501458 usd
   ==> allocated_cores=0 | idle_cores=4 | other_cores=0 | total_cores=4

Recording: https://asciinema.org/a/594177
