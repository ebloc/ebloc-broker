**Installation Instructions for Mac:**

.. code:: bash

    git clone https://github.com/ethereum/go-ethereum
    brew install go
    cd go-ethereum
    make geth

**Installation Instructions for Linux:**

Go-installation: (required for initial geth load)

.. code:: bash

    sudo add-apt-repository ppa:ubuntu-lxc/lxd-stable
    sudo apt-get update
    sudo apt-get install golang

Ethereum installation:

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

``[~] touch pass.js`` Open ``pass.js`` in your favorite text editor, and
paste following piece into it.

.. code:: bash

    admin.addPeer("enode://7f3bebdd678d5a0ebe2701b2f7858763f5ce03fc531fe989fb7bb41d2e8e1237ae5b092666171a180afba0c47f1aad055e2bf6e1287fcdc756f183902764eba2@79.1\
    23.177.145:3000");

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
