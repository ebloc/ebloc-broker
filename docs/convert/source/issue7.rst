Please install parity for following link:
https://github.com/paritytech/parity

**Dependencies:** Linux: ``$ curl https://sh.rustup.rs -sSf | sh``
Parity also requires gcc, g++, libssl-dev/openssl, libudev-dev and
pkg-config packages to be installed.

OSX:

``$ curl https://sh.rustup.rs -sSf | sh``

``source .cargo/env``

**Build from source:**

::

    # download Parity code
    $ git clone https://github.com/paritytech/parity
    $ cd parity

    # build in release mode
    $ cargo build --release

``[$] mkdir ebloc-parity && cd ebloc-parity`` Create a file called
``parity.json`` and paste following code:

::

    {
      "name": "Ebloc",
      "engine": {
        "Ethash": {
          "params": {
            "gasLimitBoundDivisor": "0x0400",
            "minimumDifficulty": "0x020000",
            "difficultyBoundDivisor": "0x0800",
            "durationLimit": "0x0d",
            "blockReward": "0x4563918244F40000",
            "registrar": "0x81a4b044831c4f12ba601adb9274516939e9b8a2",
            "homesteadTransition": "0x00",
            "eip150Transition": "0x7fffffffffffffff",
            "eip155Transition": "0x7fffffffffffffff",
            "eip160Transition": "0x7fffffffffffffff",
            "eip161abcTransition": "0x7fffffffffffffff",
            "eip161dTransition": "0x7fffffffffffffff"
          }
        }
      },
      "params": {
        "accountStartNonce": "0x00",
        "maximumExtraDataSize": "0x20",
        "minGasLimit": "0x1388",
        "networkID": "0x5B7E",
        "eip98Transition": "0x7fffffffffffffff"
      },
      "genesis": {
        "seal": {
          "ethereum": {
            "nonce": "",
            "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000"
          }
        },
        "difficulty": "0x400",
        "author": "0x3333333333333333333333333333333333333333",
        "timestamp": "0x00",
        "parentHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
        "extraData": "0x00",
        "gasLimit": "0x3B4A1B44"
      },
      "accounts": {
        "0000000000000000000000000000000000000001": { "builtin": { "name": "ecrecover", "pricing": { "linear": { "base": 3000, "word": 0 } } } },
        "0000000000000000000000000000000000000002": { "builtin": { "name": "sha256", "pricing": { "linear": { "base": 60, "word": 12 } } } },
        "0000000000000000000000000000000000000003": { "builtin": { "name": "ripemd160", "pricing": { "linear": { "base": 600, "word": 120 } } } },
        "0000000000000000000000000000000000000004": { "builtin": { "name": "identity", "pricing": { "linear": { "base": 15, "word": 3 } } } },
        "0xda1e61e853bb8d63b1426295f59cb45a34425b63": { "balance": "1000000000000000000000000000000" }
      }
    }

Create a file called ``myPrivateNetwork.txt`` and paste following lines:

.. code:: bash

    enode://7f3bebdd678d5a0ebe2701b2f7858763f5ce03fc531fe989fb7bb41d2e8e1237ae5b092666171a180afba0c47f1aad055e2bf6e1287fcdc756f183902764eba2@79.123.177.145:3000
    enode://4d331051d8fb471c87a9351b36ffb72bf445a9337727d229e03c668f99897264bf11e1b897b1561f5889825e2211b06858139fa469fdf73c64d43a567ea72479@193.140.197.126:3005
    enode://38f074f4db8e64dfbaf87984bf290eef67772a901a7113d1b62f36216be152b8450c393d6fc562a5e38f04f99bc8f439a99010a230b1d92dc1df43bf0bd00615@176.9.3.148:3000

**To run Parity:**

``Author`` is the owner of the mined block reward. You your own account
where you have created.

.. code:: bash

    parity --chain parity.json --network-id 23422 --reserved-peers myPrivateNetwork.txt --jsonrpc-apis web3,eth,net,parity,parity_accounts,traces,rpc,parity_set --rpccorsdomain localhost -ludp=debug,tcp=debug,sync=debug --author "0x75....."

To attach Geth console to Parity, (on Linux) use:
``geth attach ~/.local/share/io.parity.ethereum/jsonrpc.ipc``

On MacOS use:

.. code:: bash

    geth attach /Users/username/Library/Application\ Support/io.parity.ethereum/jsonrpc.ipc console

Open your favourite browser and type: localhost:8080 . I observe that
google-chrome it better to use with it. Its UI is much better than other
apps.

Parity's has a default wrap property: warp sync is downloading snapshots
of the state first, so you are basically synced within <60 seconds. and
after that it slowly catches up missing blocks
https://github.com/paritytech/parity/wiki/Warp-Sync
