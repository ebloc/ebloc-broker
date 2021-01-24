Guide: https://github.com/ethereum/cpp-ethereum

First, since it will create new DAG do on the home directory:
``cd && rm -rf .ethash/``

**Dependencies:**

Linux-based:

::

   sudo apt-get install libleveldb-dev libcurl4-openssl-dev libmicrohttpd-dev install libudev-dev

macOS:

::

   brew install leveldb libmicrohttpd

**Install:**

::

   git clone --recursive https://github.com/ethereum/cpp-ethereum.git
   cd cpp-ethereum

**Build:**

::

   cmake -H. -Bbuild
   cmake --build build

::

   [$]ethminer --version
    ethminer version 1.3.0 | Build: ETH_BUILD_PLATFORM/ETH_BUILD_TYPE

**To Mine:** This code will use full horse
power:\ ``sudo ./ethminer -F http://localhost:8545``.

   -t, –mining-threads Limit number of CPU/GPU miners to n (default: use
   everything available on selected platform)

``[~/cpp-ethereum]$ cd build/ethminer``
``[~/cpp-ethereum/build/ethminer]$sudo ./ethminer -F http://localhost:8545 --mining-threads 2``
