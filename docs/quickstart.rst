How to Use eBlocBroker
======================

About
-----

**eBlocBroker** is a blockchain based autonomous computational resource
broker.

-  **Website:** http://ebloc.cmpe.boun.edu.tr or
   `http://ebloc.org <http://ebloc.cmpe.boun.edu.tr>`__
-  `Documentation <http://ebloc.cmpe.boun.edu.tr:3003/index.html>`__

Build dependencies
------------------

`Geth <https://github.com/ethereum/go-ethereum/wiki/geth>`__,
`Parity <https://parity.io>`__,
`IPFS <https://ipfs.io/docs/install/>`__,
`Slurm <https://github.com/SchedMD/slurm>`__.

How to connect into Private Ethereum Blockchain (eBloc) using geth
------------------------------------------------------------------

Please follow `here <https://github.com/ebloc/eblocGeth>`__.

How to use eBlocBroker inside an Amazon EC2 Instance
----------------------------------------------------

An Amazon image (AMI Name: eBlocBroker, AMI ID: ``ami-43e6083e``) is
also available that contains ``Geth`` to connect to our local Ethereum
based blockchain system. First launch an instance using this Amazon
image, you will recieve its Public DNS hostname (IPv4).

.. code:: bash

    ssh -v -i "full/path/to/my.pem" ubuntu@Public-DNS-hostname

    eblocServer                            # To run eBloc geth-server
    cd ../eBlocBroker && python Driver.py  # To run the eBlocBroker

Create your Ethereum Account
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Inside your ``geth-client``, use:

::

    > personal.NewAccount()
    Passphrase:
    Repeat passphrase:
    "0x2384a05f8958f3490fbb8ab6919a6ddea1ca0903"

    > eth.accounts
    ["0x2384a05f8958f3490fbb8ab6919a6ddea1ca0903"]

-  Open the following file: ``$HOME/eBlocBroker/eBlocBrokerHeader.js``
   and change following line with the account you defined under
   ``COINBASE``,

``COINBASE = "0x2384a05f8958f3490fbb8ab6919a6ddea1ca0903";``

Connect into eBloc private chain using Geth: ``eblocServer``. On another
console to attach Geth console please do: ``eblocClient``. Please note
that first you have to run ``eblocServer`` and than ``eblocClient``.

.. raw:: html

   <!--- 
   ### How to create a new account


   ```bash
   parity --chain /home/ubuntu/EBloc/parity.json account new --network-id 23422 --reserved-peers /home/ubuntu/EBloc/myPrivateNetwork.txt --jsonrpc-apis web3,eth,net,parity,parity_accounts,traces,rpc,parity_set --rpccorsdomain=*

   Please note that password is NOT RECOVERABLE.
   Type password:
   Repeat password:
   e427c111f968fe4ff6593a37454fdd9abf07c490  //your address is generated
   ```

   - Inside `.profile` change `COINBASE` variable with the generated account address. For example, you could put your newly created address such as `"0xe427c111f968fe4ff6593a37454fdd9abf07c490"` into `COINBASE`. Do not forget to put `0x` at the beginning of the account.


   - Update the following file `/home/ubuntu/EBloc/password.txt` with your account's password.
   Best to make sure the file is not readable or even listable for anyone but you. You achieve this with: `chmod 700 /home/ubuntu/EBloc/password.txt`

   - Open the following file: `/home/ubuntu/eBlocBroker/eBlocBrokerHeader.js` and change following line with the account you defined under `COINBASE`, which is `web3.eth.defaultAccount = "0xe427c111f968fe4ff6593a37454fdd9abf07c490";`

   Connect into eBloc private chain using Parity: `eblocpserver`. You could also run it via `nohup eblocpserver &` on the background. On another console to attach Geth console to Parity, (on Linux) please do: `geth attach`.

   Please note that first you have to run `eblocpserver` and than `geth attach`.

   Inside Geth console when you type `eth.accounts` you should see the accounts you already created or imported.

   ```bash
   > eth.accounts
   ["0xe427c111f968fe4ff6593a37454fdd9abf07c490"]
   ```

   This line is required to update `Parity`'s enode.

   ```bash
   rm  ~/.local/share/io.parity.ethereum/network/key
   ```

   As final you should run Parity as follows which will also unlocks your account:

   ```bash
   parity --chain /home/ubuntu/EBloc/parity.json --network-id 23422 --reserved-peers /home/ubuntu/EBloc/myPrivateNetwork.txt --jsonrpc-apis web3,eth,net,parity,parity_accounts,traces,rpc,parity_set --author $COINBASE --rpccorsdomain=* --unlock "0xe427c111f968fe4ff6593a37454fdd9abf07c490" --password password.txt
   ```
   --->

Start Running Cluster using eBlocBroker
---------------------------------------

SLURM Setup:
~~~~~~~~~~~~

SLURM have to work on the background. Please run:

.. code:: bash

    sudo bash runSlurm.sh

Following example should successfully submit the job:

.. code:: bash

    cd eBlocBroker/slurmJobExample
    sbatch -N1 run.sh
    Submitted batch job 1

Running ``IPFS``, ``Parity`` and eBlocBroker scripts on the background:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    ipfs daemon &
    nohup bash eblocpserver.sh &
    cd $EBLOCBROKER
    bash runDaemon.sh

Cluster Side: How to register a cluster
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please note the following:

-  If you don't have any ``Federated Cloud ID`` or ``MiniLock ID`` give
   an empty string: ``""``.

.. code:: bash

    coreNumber         = 128;
    clusterEmail       = "ebloc@gmail.com";
    federationCloudId  = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu";
    miniLockId         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
    corePriceMinuteWei = 100; 
    ipfsID             = "QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"; //ipfs id | grep "ID"

    //RegisterCluster
    if(federationCloudId.length < 128 && clusterEmail.length < 32 && (miniLockId.length == 0 || miniLockId.length == 45))
         eBlocBroker.registerCluster(coreNumber, clusterEmail, federationCloudId, miniLockId, corePriceMinuteWei, ipfsID, {from: eth.coinbase, gas: 4500000})

    //UpdateCluster
    if(federationCloudId.length < 128 && clusterEmail.length < 32 && (miniLockId.length == 0 || miniLockId.length == 45))
        eBlocBroker.updateCluster(coreNumber, clusterEmail, federationCloudId, miniLockId, corePriceMinuteWei, ipfsID, {from: eth.coinbase, gas: 4500000}); 

    //Deregister
    eBlocBroker.deregisterCluster( {from: eth.coinbase, gas: 4500000} )

**Trigger code on start and end of the submitted job:** Cluster should
do: ``sudo chmod +x /path/to/slurmScript.sh``. This will allow script to
be readable and executable by any SlurmUser. Update following line on
the slurm.conf file:
``MailProg=/home/ubuntu/eBlocBroker/slurmScript.sh``

.. code:: bash

    sudo chmod 755 ~/.eBlocBroker/*

**How to return all available Clusters Addresses**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: bash

    eBlocBroker.getClusterAddresses();
    ["0x6af0204187a93710317542d383a1b547fa42e705"]

Client Side: How to obtain IPFS Hash of the job:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is important that first you should run IPFS daemon on the background:
``ipfs daemon &``. If it is not running, cluster is not able to get the
IPFS object from the client's node.

Example code could be seen under ``eBlocBroker/slurmJobExample``
directory:

Client should put his SLURM script inside a file called ``run.sh``.
Please note that you do not have to identify ``-n`` and ``-t``
parameters, since they will be overritten with arguments provided by the
client on the cluster side.

Target into the folder you want to submit and do: ``ipfs add -r .`` You
will see something similiar with following output:

.. code:: bash

    added QmYsUBd5F8FA1vcUsMAHCGrN8Z92TdpNBAw6rMxWwmQeMJ simpleSlurmJob/helloworld.cpp
    added QmbTzBprmFEABAWwmw1VojGLMf3nv7Z16eSgec55DYdbiX simpleSlurmJob/run.sh
    added QmXsCmg5jZDvQBYWtnAsz7rukowKJP3uuDuxfS8yXvDb8B simpleSlurmJob

-  Main folder's IPFS hash (for
   example:\ ``QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd``) would
   be used as key to the submitted ``jobKey`` to the ``eBlocBroker`` by
   the client.

.. raw:: html

   <!--- 
   - If you want to share it through gitHub, please push all files into github repository and share its web URL right after `https://github.com/`, which is `USERNAME/REPOSITORY.git`.

   For example, web URL of `https://github.com/avatar-lavventura/simpleSlurmJob.git`, you have to submit: `avatar-lavventura/simpleSlurmJob.git`.
   --->

--------------

**How to submit a job using storageTypes**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use ``contractCall/submitJob.py`` to submit your jobs. To run:
``python contractCall/submitJob.py``

**1. How to submit a job using IPFS**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: bash

    # USER Inputs----------------------------------------------------------------------
    clusterAddress   = "0x6af0204187a93710317542d383a1b547fa42e705";  
    ipfsHash         = "QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5";
    coreNum          = 1; 
    coreGasDay       = 0;
    coreGasHour      = 0;
    coreGasMin       = 10;
    jobDescription   = "Science"
    storageType      = 0; // Please note that '0' stands for IPFS repository share. Fixed.
    # ----------------------------------------------------------------------------------
    myMiniLockId     = ""; #Fixed.

**2. How to submit a job using EUDAT**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before doing this you have to be sure that you have shared your folder
with cluster's FID. Please
`follow <https://github.com/avatar-lavventura/someCode/issues/4>`__.
Otherwise your job will not be accepted.

.. raw:: html

   <!--- 
   `FederationCloudId` followed by the name of the folder your are sharing having equal symbol (`=`) in between.
   *Example:*`jobHash = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579=folderName"`
   ---->

**Script:**
'''''''''''

.. code:: bash

    # USER Inputs----------------------------------------------------------------------
    clusterAddress = "0x6af0204187a93710317542d383a1b547fa42e705";
    jobKey         = "folderName";
    coreNum        = 1;
    coreGasDay     = 0;
    coreGasHour    = 0;
    coreGasMin     = 10;
    jobDescription = "Science";
    storageType    = 1; # Please note that '1' stands for EUDAT repository share. Fixed.
    # ----------------------------------------------------------------------------------
    myMiniLockId     = ""; # Fixed

**3. How to submit a job using IPFS+miniLock**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

miniLock Setup
              

Please check following
`tutorial <https://www.npmjs.com/package/minilock-cli>`__:

Generate a miniLock ID
                      

.. code:: bash

    $ mlck id alice@example.com --save
    period dry million besides usually wild everybody
     
    Passphrase (leave blank to quit): 

You can look up your miniLock ID any time.

.. code:: bash

    $ mlck id
    Your miniLock ID: LRFbCrhCeN2uVCdDXd2bagoCM1fVcGvUzwhfVdqfyVuhi

How to encripty your folder using miniLock
                                          

.. code:: bash

    clusterMiniLockId = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ";
    encrypyFolderPath = "./ipfsCode"
    tar -cvzf $encrypyFolderPath.tar.gz $encrypyFolderPath

    mlck encrypt -f $encrypyFolderPath.tar.gz $clusterMiniLockId --passphrase="$(cat mlck_password.txt)"
    ipfs add $ncrypyFolderPath.minilock
    added QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5 message.tar.gz.minilock

**Script:**
           

.. code:: bash

    # USER Inputs----------------------------------------------------------------------
    clusterID        = "0x6af0204187a93710317542d383a1b547fa42e705"; # clusterID you would like to submit. 
    jobKey           = "QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5"
    coreNum          = 1; 
    coreGasDay       = 0;
    coreGasHour      = 0;
    coreGasMin       = 10;
    jobDescription   = "Science"
    storageType      = 2; // Please note 2 stands for IPFS with miniLock repository share. Fixed.
    myMiniLockId     = "LRFbCrhCeN2uVCdDXd2bagoCM1fVcGvUzwhfVdqfyVuhi"
    # ----------------------------------------------------------------------------------

**4. How to submit a job using GitHub**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If my github repository is
``https://github.com/avatar-lavventura/simpleSlurmJob.git``. Please
write your username followed by the folder name having '=' in between.
Example: ``avatar-lavventura=simpleSlurmJob``

.. code:: bash

    # USER Inputs----------------------------------------------------------------------
    clusterID        = "0x6af0204187a93710317542d383a1b547fa42e705"; # clusterID you would like to submit.
    jobKey           = "avatar-lavventura=simpleSlurmJob" 
    coreNum          = 1; 
    coreGasDay       = 0;
    coreGasHour      = 0;
    coreGasMin       = 10;
    jobDescription   = "Science"
    storageType      = 3 ; # Please note that 4 stands for github repository share. Fixed.
    # ----------------------------------------------------------------------------------
    myMiniLockId     = ""; # Fixed

--------------

**5. How to submit a job using Google-Drive**
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

[gdrive] (https://github.com/prasmussen/gdrive) install:
''''''''''''''''''''''''''''''''''''''''''''''''''''''''

::

    $ go get github.com/prasmussen/gdrive
    $ gopath=$(go env | grep 'GOPATH' | cut -d "=" -f 2 | tr -d '"')
    $ echo 'export PATH=$PATH:$gopath/bin' >> ~/.profile
    $ source .profile
    $ gdrive about # This line authenticates the user only once on the same node.
    Authentication needed
    Go to the following url in your browser:
    https://accounts.google.com/o/oauth2/auth?access_type=offline&client_id=...e=state
    Enter verification code:

First you have to share your folder with the cluster:

::

    folderPath='/home/prc/multiple/workingTestIpfs'
    folderName='ipfs'
    clusterToShare='aalimog1@binghamton.edu'
    gdrive upload --recursive $folderPath/$folderName
    jobKey=$(gdrive list | grep $folderName | awk '{print $1}')
    echo $jobKey # This is jobKey
    gdrive share $jobKey  --role writer --type user --email $clusterToShare

If your work is zipper under folder name such as
folderPath/folderName/RUN.zip ; please name it ``RUN.zip`` or
``RUN.tar.gz``.

--------------

.. code:: bash

    # USER Inputs----------------------------------------------------------------------
    clusterID        = "0xda1e61e853bb8d63b1426295f59cb45a34425b63"; # clusterID you would like to submit.
    jobKey           = "1-R0MoQj7Xfzu3pPnTqpfLUzRMeCTg6zG" # Please write file-Id of the uploaded file
    coreNum          = 1; 
    coreGasDay       = 0;
    coreGasHour      = 0;
    coreGasMin       = 10;
    jobDescription   = "Science"
    storageType      = 4; # Please note that 4 stands for gdrive repository share. Fixed. 
    # ----------------------------------------------------------------------------------
    myMiniLockId     = ""; # Fixed.

**How to obtain Submitted Job's Information:**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  status could be ``"QUEUED"`` or ``"RUNNING"`` or ``"COMPLETED"``
-  ``ipfsOut`` is Completed Job's folder's ipfs hash. This exists if the
   job is completed.

.. code:: bash

    clusterID="0x6af0204187a93710317542d383a1b547fa42e705"; # clusterID that you have submitted your job.
    jobHash = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579=134633894220713919382117768988457393273"
    index   = 0;      
    eBlocBroker.getJobInfo(clusterID, jobHash, index);

--------------

Events
~~~~~~

Keep track of the log of receipts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: bash

    fromBlock = eBlocBroker.getDeployedBlockNumber(); 
    var event = eBlocBroker.LogReceipt({}, {fromBlock:fromBlock, toBlock:'latest'});
    event.watch(function(error, result) {
      console.log(JSON.stringify(result));
    });

Keep track of the log of submitted jobs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: bash

    fromBlock = eBlocBroker.getDeployedBlockNumber(); 
    var event = eBlocBroker.LogJob({}, {fromBlock:fromBlock, toBlock:'latest'});
    event.watch(function(error, result) {
      console.log(JSON.stringify(result));
    });
