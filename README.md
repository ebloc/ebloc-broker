# How to Use eBlocBroker 

## About
**eBlocBroker** is a blockchain based autonomous computational resource broker.

- **Website:** [http://ebloc.cmpe.boun.edu.tr](http://ebloc.cmpe.boun.edu.tr) or [http://ebloc.org](http://ebloc.cmpe.boun.edu.tr)
- [Documentation](http://ebloc.cmpe.boun.edu.tr:3003/index.html)

## Build dependencies

[Geth](https://github.com/ethereum/go-ethereum/wiki/geth), [Parity](https://parity.io), [IPFS](https://ipfs.io/docs/install/), [Slurm](https://github.com/SchedMD/slurm).

## How to connect into Private Ethereum Blockchain (eBloc) using geth

Please follow [here](https://github.com/ebloc/eblocGeth).

## How to use eBlocBroker inside an Amazon EC2 Instance


An Amazon image (AMI Name: eBloc, AMI ID: `ami-f5c47f8a`) is also available that contains
`geth` setup to connect to our local Ethereum based blockchain system.  

### Create your Ethereum Account

Inside your `geth-client`, use:

```
> personal.NewAccount()
Passphrase:
Repeat passphrase:
"0x2384a05f8958f3490fbb8ab6919a6ddea1ca0903"

> eth.accounts
["0x2384a05f8958f3490fbb8ab6919a6ddea1ca0903"]
```

- Open the following file: `$HOME/eBlocBroker/.profile` and change following line with the account you defined under `COINBASE`, 

 `COINBASE = "0x2384a05f8958f3490fbb8ab6919a6ddea1ca0903";`

Connect into eBloc private chain using Geth: `eblocServer `. On another console to attach Geth console please do: `eblocClient`. Please note that first you have to run `eblocServer` and than `eblocClient`.


Please do following inside your Amazon instance.

```bash
$ eblocServer          # To run eBloc Etheruem node
$ nohup ipfs daemon &  # Runs IPFS daemon

## To run eBlocBroker Daemon
$ cd $HOME/eBlocBroker 
$ bash initialize.sh # Do it only once.
$ bash runDaemon.sh  
```

## Connect to eBlocBroker Contract

```bash
var address="0x8c22de03d3ce0b9dcb39617e7c31483ec484c720"
var abi=[{"constant":true,"inputs":[{"name":"userAddress","type":"address"}],"name":"isUserExist","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"clusterAddress","type":"address"},{"name":"jobKey","type":"string"},{"name":"index","type":"uint256"}],"name":"getJobInfo","outputs":[{"name":"","type":"uint8"},{"name":"","type":"uint32"},{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"clusterAddress","type":"address"}],"name":"getClusterReceivedAmount","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"jobKey","type":"string"},{"name":"index","type":"uint32"},{"name":"jobRunTimeMinute","type":"uint32"},{"name":"resultIpfsHash","type":"string"},{"name":"storageID","type":"uint8"},{"name":"endTime","type":"uint256"}],"name":"receiptCheck","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"clusterAddress","type":"address"}],"name":"getClusterReceiptSize","outputs":[{"name":"","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"userAddress","type":"address"}],"name":"getUserInfo","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"getClusterAddresses","outputs":[{"name":"","type":"address[]"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"userEmail","type":"string"},{"name":"fID","type":"string"},{"name":"miniLockID","type":"string"},{"name":"ipfsAddress","type":"string"}],"name":"registerUser","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"getDeployedBlockNumber","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"clusterAddress","type":"address"}],"name":"getClusterInfo","outputs":[{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[],"name":"deregisterCluster","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"clusterAddress","type":"address"},{"name":"jobKey","type":"string"},{"name":"core","type":"uint32"},{"name":"jobDesc","type":"string"},{"name":"coreMinuteGas","type":"uint32"},{"name":"storageID","type":"uint8"}],"name":"submitJob","outputs":[{"name":"success","type":"bool"}],"payable":true,"stateMutability":"payable","type":"function"},{"constant":true,"inputs":[{"name":"clusterAddress","type":"address"},{"name":"index","type":"uint32"}],"name":"getClusterReceiptNode","outputs":[{"name":"","type":"uint256"},{"name":"","type":"int32"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"coreNumber","type":"uint32"},{"name":"clusterEmail","type":"string"},{"name":"fID","type":"string"},{"name":"miniLockID","type":"string"},{"name":"coreMinutePrice","type":"uint256"},{"name":"ipfsAddress","type":"string"}],"name":"updateCluster","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"clusterAddress","type":"address"}],"name":"isClusterExist","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"clusterAddress","type":"address"},{"name":"jobKey","type":"string"}],"name":"getJobSize","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"coreNumber","type":"uint32"},{"name":"clusterEmail","type":"string"},{"name":"fID","type":"string"},{"name":"miniLockID","type":"string"},{"name":"coreMinutePrice","type":"uint256"},{"name":"ipfsAddress","type":"string"}],"name":"registerCluster","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"jobKey","type":"string"},{"name":"index","type":"uint32"},{"name":"stateID","type":"uint8"},{"name":"startTime","type":"uint256"}],"name":"setJobStatus","outputs":[{"name":"success","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"name":"clusterAddress","type":"address"},{"name":"jobKey","type":"string"},{"name":"index","type":"uint32"}],"name":"refund","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"inputs":[],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"name":"cluster","type":"address"},{"indexed":false,"name":"jobKey","type":"string"},{"indexed":false,"name":"index","type":"uint256"},{"indexed":false,"name":"storageID","type":"uint8"},{"indexed":false,"name":"desc","type":"string"}],"name":"LogJob","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"cluster","type":"address"},{"indexed":false,"name":"jobKey","type":"string"},{"indexed":false,"name":"index","type":"uint256"},{"indexed":false,"name":"recipient","type":"address"},{"indexed":false,"name":"received","type":"uint256"},{"indexed":false,"name":"returned","type":"uint256"},{"indexed":false,"name":"endTime","type":"uint256"},{"indexed":false,"name":"resultIpfsHash","type":"string"},{"indexed":false,"name":"storageID","type":"uint8"}],"name":"LogReceipt","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"cluster","type":"address"},{"indexed":false,"name":"coreNumber","type":"uint32"},{"indexed":false,"name":"clusterEmail","type":"string"},{"indexed":false,"name":"fID","type":"string"},{"indexed":false,"name":"miniLockID","type":"string"},{"indexed":false,"name":"coreMinutePrice","type":"uint256"},{"indexed":false,"name":"ipfsAddress","type":"string"}],"name":"LogCluster","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"cluster","type":"address"},{"indexed":false,"name":"userEmail","type":"string"},{"indexed":false,"name":"fID","type":"string"},{"indexed":false,"name":"miniLockID","type":"string"},{"indexed":false,"name":"ipfsAddress","type":"string"}],"name":"LogUser","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"clusterAddress","type":"address"},{"indexed":false,"name":"jobKey","type":"string"},{"indexed":false,"name":"index","type":"uint32"}],"name":"LogRefund","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"clusterAddress","type":"address"},{"indexed":false,"name":"jobKey","type":"string"},{"indexed":false,"name":"index","type":"uint32"},{"indexed":false,"name":"startTime","type":"uint256"}],"name":"LogSetJob","type":"event"}]
var eBlocBroker = web3.eth.contract(abi).at(address);
```

## Start Running Cluster using eBlocBroker

### SLURM Setup:
SLURM have to work on the background. Please run: 

```bash 
sudo bash runSlurm.sh
```

Following example should successfully submit the job:

```bash
cd eBlocBroker/slurmJobExample
sbatch -N1 run.sh
Submitted batch job 1
```

### Cluster Side: How to register a cluster

Please note the following: 

- If you don't have any `Federated Cloud ID` or `MiniLock ID` give an empty string: `""`. You can use `contractCall/registerCluster.py` to submit your jobs. To run: `python3 contractCall/registerCluster.py`.  

```bash
coreNumber         = 128;
clusterEmail       = "ebloc@gmail.com";
federationCloudId  = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu";
miniLockId         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
corePriceMinuteWei = 100; 
ipfsID             = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"; 
python3 contractCall/registerCluster.py $coreNumber $clusterEmail $federationCloudId $miniLockId $corePriceMinuteWei $ipfsID
```

#### **How to return all available Clusters Addresses**

```
$ python3 contractCall/getClusterAddresses.py
```

### Client Side: How to obtain IPFS Hash of the job:

It is important that first you should run IPFS daemon on the background: `ipfs daemon &`. If it is not running, cluster is not able to get the IPFS object from the client's node.

Example code could be seen under `eBlocBroker/slurmJobExample` directory:

Client should put his SLURM script inside a file called `run.sh`. Please note that you do not have to identify `-n` and `-t` parameters, since they will be overritten with arguments provided by the client on the cluster side.

Target into the folder you want to submit and do: `ipfs add -r .` You will see something similiar with following output:

```bash
added QmYsUBd5F8FA1vcUsMAHCGrN8Z92TdpNBAw6rMxWwmQeMJ simpleSlurmJob/helloworld.cpp
added QmbTzBprmFEABAWwmw1VojGLMf3nv7Z16eSgec55DYdbiX simpleSlurmJob/run.sh
added QmXsCmg5jZDvQBYWtnAsz7rukowKJP3uuDuxfS8yXvDb8B simpleSlurmJob
```

- Main folder's IPFS hash (for example:`QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd`) would be used as key to the submitted `jobKey` to the `eBlocBroker` by the client.

-----------

### **How to submit a job using storageTypes**

In order to submit your job each user should already registered into eBlocBroker.You can use `contractCall/registerUser.py` to register. To run: `python3 contractCall/registerUser.py`. Please update followin arguments inside `registerUser.py` file.

`account`, `userEmail`, `federationCloudID`, `miniLockID`, and `ipfsAddress`.

After registiration is done,  each user should authenticate his ORCID id using following [link](http://ebloc.cmpe.boun.edu.tr/orcid-authentication/index.php).

-----------

Later, you can use `contractCall/submitJob.py` to submit your jobs. To run: `python3 contractCall/submitJob.py`.

#### **1. How to submit a job using IPFS**

Please update following arguments inside `submitJob.py` file.

```bash
clusterAddress   = "0x6af0204187a93710317542d383a1b547fa42e705";  
ipfsHash         = "QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5";
coreNum          = 1; 
coreGasDay       = 0;
coreGasHour      = 0;
coreGasMin       = 10;
jobDescription   = "Science"
storageType      = 0; # Please note that '0' stands for IPFS repository share. Fixed.
```

#### **2. How to submit a job using EUDAT**

Before doing this you have to be sure that you have shared your folder with cluster's FID. Please [follow](https://github.com/avatar-lavventura/someCode/issues/4). Otherwise your job will not be accepted. Please update following arguments inside `submitJob.py` file.

```bash
clusterAddress = "0x6af0204187a93710317542d383a1b547fa42e705";
jobKey         = "folderName";
coreNum        = 1;
coreGasDay     = 0;
coreGasHour    = 0;
coreGasMin     = 10;
jobDescription = "Science";
storageType    = 1; # Please note that '1' stands for EUDAT repository share. Fixed.
```

#### **3. How to submit a job using IPFS+miniLock**

###### miniLock Setup

Please check following [tutorial](https://www.npmjs.com/package/minilock-cli). Do following code only to generate miniLock ID once and do not lose your passphrase:

```bash
$ mlck id alice@gmail.com --save --passphrase='bright wind east is pen be lazy usual'
```

You can look up your miniLock ID any time.

```bash
$ mlck id
Your miniLock ID: LRFbCrhCeN2uVCdDXd2bagoCM1fVcGvUzwhfVdqfyVuhi
```

###### How to decript your folder using miniLock

```bash
mlck decrypt -f fileName --passphrase="$(cat mlck_password.txt)" --output-file=./output.tar.gz
```
---------

Please update following arguments inside `submitJob.py` file.

```bash
clusterID        = "0x6af0204187a93710317542d383a1b547fa42e705"; # clusterID you would like to submit. 
jobKey           = "QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5"
coreNum          = 1; 
coreGasDay       = 0;
coreGasHour      = 0;
coreGasMin       = 10;
jobDescription   = "Science"
storageType      = 2; # Please note 2 stands for IPFS with miniLock repository share. Fixed.
```

#### **4. How to submit a job using GitHub**

If my github repository is `https://github.com/avatar-lavventura/simpleSlurmJob.git`. Please write your username followed by the folder name having '=' in between. Example: `avatar-lavventura=simpleSlurmJob`. Please update following arguments inside `submitJob.py` file. 

```bash
clusterID        = "0x6af0204187a93710317542d383a1b547fa42e705"; # clusterID you would like to submit.
jobKey           = "avatar-lavventura=simpleSlurmJob" 
coreNum          = 1; 
coreGasDay       = 0;
coreGasHour      = 0;
coreGasMin       = 10;
jobDescription   = "Science"
storageType      = 3 ; # Please note that 3 stands for github repository share. Fixed.
```
-------------------------

#### **5. How to submit a job using Google-Drive**

##### [gdrive] (https://github.com/prasmussen/gdrive) install:

```
$ go get github.com/prasmussen/gdrive
$ gopath=$(go env | grep 'GOPATH' | cut -d "=" -f 2 | tr -d '"')
$ echo 'export PATH=$PATH:$gopath/bin' >> ~/.profile
$ source .profile
$ gdrive about # This line authenticates the user only once on the same node.
Authentication needed
Go to the following url in your browser:
https://accounts.google.com/o/oauth2/auth?access_type=offline&client_id=...e=state
Enter verification code:
```

First you have to share your folder with the cluster:

```
folderPath='/home/prc/multiple/workingTestIpfs'
folderName='ipfs'
clusterToShare='aalimog1@binghamton.edu'
gdrive upload --recursive $folderPath/$folderName
jobKey=$(gdrive list | grep $folderName | awk '{print $1}')
echo $jobKey # This is jobKey
gdrive share $jobKey  --role writer --type user --email $clusterToShare
```

If your work is compressed under folder name such as folderPath/folderName/RUN.zip ; please name it `RUN.zip` or `RUN.tar.gz`.

---------

Please update following arguments inside `submitJob.py` file.

```bash
clusterID        = "0xda1e61e853bb8d63b1426295f59cb45a34425b63"; # clusterID you would like to submit.
jobKey           = "1-R0MoQj7Xfzu3pPnTqpfLUzRMeCTg6zG" # Please write file-Id of the uploaded file
coreNum          = 1; 
coreGasDay       = 0;
coreGasHour      = 0;
coreGasMin       = 10;
jobDescription   = "Science"
storageType      = 4; # Please note that 4 stands for gdrive repository share. Fixed. 
```


### **How to obtain Submitted Job's Information:**

You can use `contractCall/getJobInfo.py` to submit your jobs. To run: `python3 contractCall/getJobInfo.py`

```bash
clusterID="0x6af0204187a93710317542d383a1b547fa42e705"; # clusterID that you have submitted your job.
jobKey = "134633894220713919382117768988457393273"
index   = 0;   
python3 contractCall/getJobInfo.py $clusterID $jobKey $index
```

- status of the job could be `QUEUED`, `REFUNDED`, `RUNNING`, `PENDING` or `COMPLETED`. 

-----------

### Events

#### Keep track of the log of receipts

```bash
fromBlock = eBlocBroker.getDeployedBlockNumber(); 
var event = eBlocBroker.LogReceipt({}, {fromBlock:fromBlock, toBlock:'latest'});
event.watch(function(error, result) {
  console.log(JSON.stringify(result));
});
```
#### Keep track of the log of submitted jobs

```bash
fromBlock = eBlocBroker.getDeployedBlockNumber(); 
var event = eBlocBroker.LogJob({}, {fromBlock:fromBlock, toBlock:'latest'});
event.watch(function(error, result) {
  console.log(JSON.stringify(result));
});
```
























<!--- 
OLD
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