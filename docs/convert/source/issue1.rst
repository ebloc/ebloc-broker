**How to connect into Private Ethereum Blockchain (eBloc)**
===========================================================

**Geth**
--------

**Preinstallations**
~~~~~~~~~~~~~~~~~~~~

**Installation Instructions for Mac:**

.. code:: bash

    git clone https://github.com/ethereum/go-ethereum
    brew install go
    cd go-ethereum
    make geth

**Installation Instructions for Linux:**

Go-installation (go-ethereum requires go version 1.7+.):

.. code:: bash

    tar -zxvf  go1.7.1.linux-amd64.tar.gz -C /usr/local/
    sudo tar -zxvf  go1.7.1.linux-amd64.tar.gz -C /usr/local/
    export PATH=$PATH:/usr/local/go/bin
    cp  /usr/local/go/src/go /usr/bin/go

**Geth installation:**

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

**eBloc Setup on Linux and macOS:**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    git clone https://github.com/ebloc/MyEthereumEbloc_geth.git
    cd MyEthereumEbloc_geth
    ebloc_path="$PWD";
    sudo geth --datadir="$ebloc_path" account new

Your new account is locked with a password. Please give a password. Do
not forget this password. Please enter a difficult passphrase for your
account.

.. code:: bash

    [~] sudo geth --datadir="$ebloc_path" init CustomGenesis.json
    WARN [10-06|11:21:38] No etherbase set and no accounts found as default
    INFO [10-06|11:21:38] Allocated cache and file handles         database=/Users/user/MyEthereumEbloc/geth/chaindata cache=16 handles=16
    INFO [10-06|11:21:38] Writing custom genesis block
    INFO [10-06|11:21:38] Successfully wrote genesis state         database=chaindata                      hash=a6e0e1...dab438
    INFO [10-06|11:21:38] Allocated cache and file handles         database=/Users/user/MyEthereumEbloc/geth/lightchaindata cache=16 handles=16
    INFO [10-06|11:21:38] Writing custom genesis block
    INFO [10-06|11:21:38] Successfully wrote genesis state         database=lightchaindata                      hash=a6e0e1...dab438

::

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

    [geth]> admin.addPeer("enode://4d331051d8fb471c87a9351b36ffb72bf445a9337727d229e03c668f99897264bf11e1b897b1561f5889825e2211b06858139fa469fdf73c64d43a567ea72479@193.140.197.95:3000");
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

To check your account using ``geth``:

.. code:: bash

    [geth]> primary = eth.accounts[0]
    "0x42760ddded01a938666a34444e478b710d43cb5a"]
    [geth] web3.fromWei(web3.eth.getBalance(primary));
    0                             //Your balance will increase when you mine.
    [geth]> web3.fromWei(web3.eth.getBalance("0xda1e61e853bb8d63b1426295f59cb45a34425b63"));
    46221.847517764296887374      //This is the some account active on the Blockchain. If you are connected into eBloc, you should see it.

If you would like to start your miner, just type following inside
``geth``: ``miner.start()`` .To stop mining: ``miner.stop()``

You could also decide how many CPU you would like to invest to mine. For
example, following line will add additional 1 CPU. ``miner.start(1)``

**Helpful Script:**
~~~~~~~~~~~~~~~~~~~

Please update ``ebloc_path`` variable on ``server.sh`` and ``client.sh``
files with path of ``MyEthereumEbloc`` folder. **To run:**
``sudo bash server.sh`` Now open a new terminal and run:
``bash client.sh``. ``net`` should return minimum 1.
