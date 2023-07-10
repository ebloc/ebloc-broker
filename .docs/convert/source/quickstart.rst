Quickstart
==========

This page provides a quick overview of how to use ``ebloc-broker`` in
Docker container using IPFS to share files/folders. For this example to
work, we need a linux or macOS instance that will run 2 docker
instances, one for requester and other for the provider.

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

IPFS Bridge
~~~~~~~~~~~

In the both docker instances IPFS nodes are unable to connect to each
other if the their linked ports [ ``4003``, ``4101`` ] are closed on the
main node. In order to overcome this, we have to install ``ipfs`` into
main node and connect it into Ipfs node that is running on the both
docker instances.

In each container select one of the address from
``ipfs id | grep "/tcp/" | sed -e 's/^\s*//'=. And connect into them from the main node using =ipfs swarm connect <address>``.

Provider
--------

First run one time:
``/workspace/ebloc-broker/broker/eblocbroker_scripts/update_provider_info.py``.
Example output:

.. code:: bash

   $ /workspace/ebloc-broker/broker/eblocbroker_scripts/update_provider_info.py
   ## address=0xe953A99FF799e6dA23948Ca876FCe3f264447De8
   ## gmail=
   ## ipfs_address=/ip4/x.x.x.x/tcp/4001/p2p/12D3KooWBvXo9ycG5BreJyLK5C9oDer9UVZX8VMMdAXS4usCrKvr
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
   ==> Is transaction successfully deployed?  [ok]

Followed by ``eblocbroker driver --no-thread``.

.. code:: bash

   $ eblocbroker driver --no-thread
   =================================================== provider session starts ====================================================
   2023-07-01 21:04 -- is_threading=False -- pid=2649 -- whoami=root -- slurm_user=root
   provider_address: 0x4cd57387cc4414be8cece4e6ab84a7dd641eab25
   rootdir: /workspace/ebloc-broker
   logfile: /root/.ebloc-broker/provider.log
   ipfs_id: /ip4/x.x.x.x/tcp/4001/p2p/12D3KooWSp3YgCs4GxCeQWcPBE1MvG9kYZCXdATsx7zaN9Uh1Jhy
   ipfs_repo_dir: /root/.ipfs
   Attached to host RPC client listening at 'http://berg-cmpe-boun.duckdns.org:8545'

   ==> is_web3_connected=True
   ==> active_network_id=bloxberg
   ==> left_of_block_number=21072479
   ==> latest_block_number=21073284
   🍺  Connected into bloxberg
   ## checking slurm...  [ok]
   groupadd: group 'eblocbroker' already exists
   ==> mongod is already running on the background
   ==> contract_address=0x9c7570e55d6414561800d72045a72b26a5a9e639
   ==> account_balance=93163688 gwei ≈ 0.09 ether
   ==> Ebb_token_balance=1999.707556 usd
   ==> allocated_cores=0 | idle_cores=2 | other_cores=0 | total_cores=2
   [  Sun 07/02 00:07:13 AM  ] waiting job events since bn=21073284 -- counter=0:02:18 ...

Recording: https://asciinema.org/a/594177

Requester
---------

Submit your first job:

First replace provider address in the file
``/workspace/ebloc-broker/broker/ipfs/job_docker.yaml``. You can use
``nano`` as editor.

Then submit the job using:

.. code:: bash

   eblocbroker submit /workspace/ebloc-broker/broker/ipfs/job_docker.yaml

--------------

Example:

.. code:: bash

   $ eblocbroker submit /workspace/ebloc-broker/broker/ipfs/job_docker.yaml
   > requester_address=0x30F02cecF3e824F963CfA05270c8993A49703D55
   ==> attemptting to submit job (/workspace/ebloc-broker/.test_eblocbroker/source_code_without_data) using IPFS
   ==> submitting source code through IPFS
    1.07 KiB / 1.07 KiB [============================================================================================] 100.00%QmNziqjjJ4dQnDiEz1PU1oJRcfQTF2L24yDrxg5iD23e8L
   bash: /root/ebloc-broker/broker/bash_scripts/machine.sh: No such file or directory
   ==> ipfs_hash=QmNziqjjJ4dQnDiEz1PU1oJRcfQTF2L24yDrxg5iD23e8L | md5sum=e72183c36c0d576ea9beb6713dc06a19
   => Entered into the cost calculation for provider=0x08b003717bfab7a80b17b51c32223460fe9efe2a
    => is_private={'QmNziqjjJ4dQnDiEz1PU1oJRcfQTF2L24yDrxg5iD23e8L': False}
    => price_core_min=0.001 usd
    => price_data_transfer=0.000001 usd
    => price_storage=0.000001 usd
    => price_cache=0.000001 usd
   {
   │ job_price=0.001001 usd for provider=0x08b003717bfab7a80b17b51c32223460fe9efe2a
   │   * computational=0.001 usd
   │   * cache=0 usd
   │   * storage=0 usd
   │       * in=0 usd
   │   * data_transfer=0.000001 usd
   │       * in=0 usd
   │       * out=0.000001 usd
   }
   -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
   => provider_to_share=0x08b003717bFab7a80b17B51C32223460Fe9EfE2A | best_price=0.001001 usd
   ==> Submitting the job(QmNziqjjJ4dQnDiEz1PU1oJRcfQTF2L24yDrxg5iD23e8L)
   {
   │   'path': PosixPath('/workspace/ebloc-broker/.test_eblocbroker/source_code_without_data'),
   │   'code_hash': 'QmNziqjjJ4dQnDiEz1PU1oJRcfQTF2L24yDrxg5iD23e8L',
   │   'folder_size_mb': 0,
   │   'storage_ids': 'IPFS',
   │   'cache_type': 'PUBLIC'
   }

   Transaction sent: 0x67c73476edd66de59f1ae86c47ff5afad980a39c768d15c9051c6742c719e4a9
     Gas price: 1.2 gwei   Gas limit: 9980000   Nonce: 159
     USDTmy.approve confirmed   Block: 21081621   Gas used: 44136 (0.44%)

   Transaction sent: 0x78a988c050bb6c284fbde0a146c7e7f78a435c1eccef05accf8d2c7aaca2e531
     Gas price: 1.2 gwei   Gas limit: 9980000   Nonce: 160
     eBlocBroker.submitJob confirmed   Block: 21081622   Gas used: 184210 (1.85%)

   tx_hash=0x78a988c050bb6c284fbde0a146c7e7f78a435c1eccef05accf8d2c7aaca2e531
   tx={
   │   'blockHash': HexBytes('0xcbb835e9da54f42994763631c0a7bbd2c97b9d6c646cb224a52b078d2340d9f2'),
   │   'blockNumber': 21081622,
   │   'cumulativeGasUsed': 184210,
   │   'from': '0x30F02cecF3e824F963CfA05270c8993A49703D55',
   │   'gasUsed': 184210,
   │   'logs': [...],
   │   'status': 1,
   │   'to': '0x9C7570E55d6414561800D72045A72B26A5a9E639',
   │   'transactionHash': HexBytes('0x78a988c050bb6c284fbde0a146c7e7f78a435c1eccef05accf8d2c7aaca2e531'),
   │   'transactionIndex': 0
   }
   => Is transaction successfully deployed?  [ok]
   job_info={
   │   'provider': '0x08b003717bFab7a80b17B51C32223460Fe9EfE2A',
   │   'owner': '0x30F02cecF3e824F963CfA05270c8993A49703D55',
   │   'jobKey': 'QmNziqjjJ4dQnDiEz1PU1oJRcfQTF2L24yDrxg5iD23e8L',
   │   'index': 1,
   │   'cloudStorageID': [0],
   │   'sourceCodeHash': [
   │   │   b'\t\xc0\xbe\x08\xd9\xfe\x10E\x12\x877\xfd\x94\'"\xee\x9f\x82\xa2*\x99\xd7\xedf\x8ak\xdf\x92\xeb\xd5\xf7\xfd'
   │   ],
   │   'cacheType': [0],
   │   'core': [1],
   │   'runTime': [1],
   │   'received': 100100,
   │   'refunded': 0
   }

Than copy the generated IPFS hash on the 4th line which is the actual
``jobKey`` of the job:
``QmNziqjjJ4dQnDiEz1PU1oJRcfQTF2L24yDrxg5iD23e8L.``

.. code:: bash

   ...
   ==> ipfs_hash=QmNziqjjJ4dQnDiEz1PU1oJRcfQTF2L24yDrxg5iD23e8L | md5sum=e72183c36c0d576ea9beb6713dc06a19
   ...
   job_info={
   │   ...
   │   'jobKey': 'QmNziqjjJ4dQnDiEz1PU1oJRcfQTF2L24yDrxg5iD23e8L',
   │   ...
   }

On the main node do:
``ipfs get QmNziqjjJ4dQnDiEz1PU1oJRcfQTF2L24yDrxg5iD23e8L``. This will
transfer file to your main node and from there to the provider node.
