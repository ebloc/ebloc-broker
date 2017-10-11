**How to connect Ethereum eBloc private blockchain**
====================================================

**Geth**
--------

**Preinstallations:**
~~~~~~~~~~~~~~~~~~~~~

**Installation Instructions for Mac:**

.. code:: bash

    git clone https://github.com/ethereum/go-ethereum
    brew install go
    cd go-ethereum
    make geth

**Installation Instructions for Linux:**

Go-installation (go-ethereum requires go version 1.7+.):

.. code:: bash

    sudo apt-get install python-software-properties 
    sudo add-apt-repository ppa:duh/golang
    sudo apt-get update
    sudo apt-get install golang

**Ethereum installation:**

.. code:: bash

    sudo apt-get install git
    git clone https://github.com/ethereum/go-ethereum
    sudo apt-get install -y build-essential libgmp3-dev golang
    cd go-ethereum/
    git pull
    make geth

After go-ethereum is installed copy ``geth`` into\ ``/usr/local/bin``:
Navigate into folder that go-ethereum is installed.

.. code:: bash

    [~] ls go-ethereum/build/bin
    geth
    [~] sudo cp build/bin/geth /usr/local/bin/
    [~] which geth
    /usr/local/bin/geth

Now when you just type ``geth``, it should work.

--------------

**eBloc on Linux and macOS Private Ethereum Setup:**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    mkdir MyEthereumEbloc
    cd MyEthereumEbloc
    ebloc_path="$PWD";
    sudo geth --datadir="$ebloc_path" account new

Your new account is locked with a password. Please give a password. Do
not forget this password. Passphrase: //!! Enter a difficult password
for your account !!

Create an empty file called CustomGenesis.json:
``[~] touch CustomGenesis.json`` Open the\ ``CustomGenesis.json`` in
your favorite text editor, and paste following piece into it.

.. code:: bash

    {
        "config": {
            "homesteadBlock": 0
        },
        "timestamp": "0x0",
        "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "extraData": "0x00",
        "gasLimit": "0x3B4A1B44",
        "difficulty": "0x400",
        "mixhash": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "coinbase": "0x3333333333333333333333333333333333333333",
        "alloc": {
            "0xda1e61e853bb8d63b1426295f59cb45a34425b63":
            { "balance": "1000000000000000000000000000000" }
        }
    }

.. code:: bash

    [~] sudo geth --datadir="$ebloc_path" init CustomGenesis.json
    WARN [10-06|11:21:38] No etherbase set and no accounts found as default
    INFO [10-06|11:21:38] Allocated cache and file handles         database=/Users/user/MyEthereumEbloc/geth/chaindata cache=16 handles=16
    INFO [10-06|11:21:38] Writing custom genesis block
    INFO [10-06|11:21:38] Successfully wrote genesis state         database=chaindata                      hash=a6e0e1...dab438
    INFO [10-06|11:21:38] Allocated cache and file handles         database=/Users/user/MyEthereumEbloc/geth/lightchaindata cache=16 handles=16
    INFO [10-06|11:21:38] Writing custom genesis block
    INFO [10-06|11:21:38] Successfully wrote genesis state         database=lightchaindata                      hash=a6e0e1...dab438

    [~] sudo geth --fast --networkid 23422 --datadir="$ebloc_path" --rpc --rpcaddr "localhost" --rpccorsdomain="*" --rpcport="8545" console
    Welcome to the Geth JavaScript console!

    instance: Geth/v1.7.0-stable-6c6c7b2a/darwin-amd64/go1.9
     modules: admin:1.0 debug:1.0 eth:1.0 miner:1.0 net:1.0 personal:1.0 rpc:1.0 txpool:1.0 web3:1.0

    > 

.. code:: bash

    [geth]> net
    {
    listening: true,
    peerCount: 0,
    version: "23422",
    getListening: function(callback),
    getPeerCount: function(callback),
    getVersion: function(callback)
    }

``peerCount`` should be **1**, if you are successfully connected into
eBloc.

.. code:: bash

    [geth]> admin.addPeer("enode://7f3bebdd678d5a0ebe2701b2f7858763f5ce03fc531fe989fb7bb41d2e8e1237ae5b092666171a180afba0c47f1aad055e2bf6e1287fcdc756f183902764eba2@79.123.177.145:3000?discport=0");
    [geth]> net
    {
    listening: true,
    peerCount: 1,
    version: "23422",
    getListening: function(callback),
    getPeerCount: function(callback),
    getVersion: function(callback)
    }
    > I0215 11:38:30.852837 eth/downloader/downloader.go:326] Block synchronisation started
    I0215 11:38:32.409662 core/blockchain.go:1064] imported   41 blocks,     0 txs (  0.000 Mg) in 805.525ms ( 0.000 Mg/s). #1401 [1e5a0d22... / 28f66e6b...]
    I0215 11:38:32.436446 core/blockchain.go:1064] imported   50 blocks,     0 txs (  0.000 Mg) in  26.172ms ( 0.000 Mg/s). #1451 [b0a79eeb... / ecaada4b...]
    I0215 11:38:32.554453 core/blockchain.go:1064] imported  293 blocks,     0 txs (  0.000 Mg) in 115.579ms ( 0.000 Mg/s). #1744 [ff3e8799... / 44aa42ef...]

Now open a new terminal and open a client:

.. code:: bash

    [~] sudo geth --datadir "$ebloc_path" attach ipc:$ebloc_path/geth.ipc console
    Welcome to the Geth JavaScript console!

    instance: Geth/v1.5.7-stable-da2a22c3/darwin/go1.7.4
    modules: admin:1.0 debug:1.0 eth:1.0 miner:1.0 net:1.0 personal:1.0 rpc:1.0 txpool:1.0 web3:1.0

    [geth]> net
    {
    listening: true,
    peerCount: 1,
    version: "23422",
    getListening: function(callback),
    getPeerCount: function(callback),
    getVersion: function(callback)
    }

To check your account inside ``geth``:

.. code:: bash

    [geth]> primary = eth.accounts[0]
    "0x42760ddded01a938666a34444e478b710d43cb5a"]
    [geth] web3.fromWei(web3.eth.getBalance(primary));
    0                             //Your balance will increase when you mine.
    [geth]> web3.fromWei(web3.eth.getBalance("0xda1e61e853bb8d63b1426295f59cb45a34425b63"));
    46221.847517764296887374      //This is the some account active on the Blockchain. If you are connected into eBloc, you should see it.

If you would like to start your miner, just type following:
``[geth]> miner.start()``

To stop mining: ``[geth]> miner.stop()``

You could also decide how many CPU you would like to invest to mine.
This will add additional 1 CPU. ``[geth]> miner.start(1)``

Not: You could send your transactions without starting your miner.
Please double check to run ``geth`` without having ``--nodiscover``
flag.

--------------

**Helpful Script:**
~~~~~~~~~~~~~~~~~~~

``[~] touch pass.js`` Open ``pass.js`` in your favorite text editor, and
paste following piece into it.

.. code:: bash

    admin.addPeer("enode://7f3bebdd678d5a0ebe2701b2f7858763f5ce03fc531fe989fb7bb41d2e8e1237ae5b092666171a180afba0c47f1aad055e2bf6e1287fcdc756f183902764eba2@79.123.177.145:3000");
    admin.addPeer("enode://4d331051d8fb471c87a9351b36ffb72bf445a9337727d229e03c668f99897264bf11e1b897b1561f5889825e2211b06858139fa469fdf73c64d43a567ea72479@193.140.197.95:3000");
    admin.addPeer("enode://9fbac6e71e1478506987872b7d3d6de19681527971ae243044daa44221a99ce5944839cd4057133f18b3610f5c59bb2fd7077fafa208d8eb52918faf06782d48@79.123.177.145:3000");

Create an empty file called ``start_server.sh``:
``[~] touch start_server.sh`` Open ``start_server.sh`` in your favorite
text editor, and paste following piece into it.

.. code:: bash

    #!/bin/bash

    ebloc_path="/Users/avatar/Library/MyEthereumEbloc";   #PLEASE update the path of yours

    nohup geth --fast --networkid 23422 --datadir="$ebloc_path" --rpc --rpcaddr "localhost" --rpccorsdomain="*" --rpcport="8545" --autodag=false &

    sleep 5

    pass_dir="/Users/avatar/pass.js"; #PLEASE update the path of pass.js
    echo 'loadScript("$pass_dir")' | sudo geth --datadir "$ebloc_path" attach ipc:$ebloc_path/geth.ipc console
    echo 'net'  | sudo geth --datadir "$ebloc_path" attach ipc:$ebloc_path/geth.ipc console
    echo 'miner.stopAutoDAG()'   | sudo geth --datadir "$ebloc_path" attach ipc:$ebloc_path/geth.ipc console

Create an empty file called ``start_client.sh``:
``[~] touch start_client.sh`` Open ``start_client.sh`` in your favorite
text editor, and paste following piece into it.

.. code:: bash

    #!/bin/bash
    ebloc_path="/Users/avatar/Library/MyEthereumEbloc";   #PLEASE update the path of yours
    sudo geth --datadir "$ebloc_path" attach ipc:$ebloc_path/geth.ipc console

To run: ``sudo bash start_server.sh`` Now open a new terminal and run:
``bash client.sh``. ``net`` should return 1.
