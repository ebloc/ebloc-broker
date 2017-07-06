# eBlocBroker

## About
Recently, peer-to-peer based blockchain infrastructures have emerged as disruptive technologies and have lead to the realization of crypto-currencies and smart contracts that can used in a globally trustless manner. eBlocBroker is a blockchain based autonomous computational resource broker

----

## Build dependencies

geth, parity, [IPFS](https://ipfs.io/docs/install/)

## Using via Amazon AWS:

```bash
mkdir ~/ebloc-amazon
sshfs -o IdentityFile=full/path/to/my.pem ubuntu@Public-DNS-hostname:/home/ubuntu ~/ebloc-amazon
cd ~/ebloc-amazon

#On an another console do:
ssh -v -i "full/path/to/my.pem" ubuntu@Public-DNS-hostname
```

**Create New Account:**

```bash
> parity --chain /home/ubuntu/EBloc/parity.json account new --network-id 23422 --reserved-peers /home/ubuntu/EBloc/myPrivateNetwork.txt --jsonrpc-apis web3,eth,net,parity,parity_accounts,traces,rpc,parity_set --author $COINBASE --rpccorsdomain=*
Please note that password is NOT RECOVERABLE.
Type password:
Repeat password:
e427c111f968fe4ff6593a37454fdd9abf07c490
```

- Inside `.profile` change `COINBASE` variable with the account owner of the mined block reward. For example, you could but your newly created account: `"0xe427c111f968fe4ff6593a37454fdd9abf07c490"` into `COINBASE`. Do not forget to put `0x` at the beginning of the account.


- Update following file `/home/ubuntu/EBloc/password.txt` with your account's password, that is stored under `COINBASE`: 
Best to make sure the file is not readable or even listable for anyone but you. You achieve this with: `chmod 700 /home/ubuntu/EBloc/password.txt`

- Open following file: `/home/ubuntu/eBlocBroker/eBlocHeader.js` and change following line with the account you defined under `COINBASE`: `web3.eth.defaultAccount = "0xe427c111f968fe4ff6593a37454fdd9abf07c490";`

Connect into eBloc private chain using Parity: `eblocpserver`. You could also run it via `nohup eblocpserver &` on the background. On another console to attach Geth console to Parity, (on Linux) please do: `geth attach ~/.local/share/io.parity.ethereum/jsonrpc.ipc`. Its alias is: `eblocpclient`. 

Please note that first you have to run `eblocpserver` and than `eblocpclient`.

Inside Geth console when you type `eth.accounts` you should see the accounts you already created or imported.

```bash
> eth.accounts
["0xe427c111f968fe4ff6593a37454fdd9abf07c490"]
```

**Required path changes you have to do on the script files:**

export EBLOCBROKER=/home/netlab/contract

Additinoal changes have to make on: since SLURM script functon won't able to access .profile file.
startCode.py endCode.py slurmScript.sh

###Start Running Cluster using eBlocBroker

**First SLURM have to work on the background:**

```bash 
mkdir /tmp/slurmstate
sudo slurmd
sudo munged -f
/etc/init.d/munge start #Do to Amazon AWS, you may need to create new user with a password.
sudo slurmdbd
sudo slurmctld -c
```

Following example should successfully submit the job:

```bash
cd /home/ubuntu/slurmTest
sbatch -U science -N1 run.sh
Submitted batch job 1
```

Running `Parity` and eBlocBroker scripts on the background:

```bash
nohup eblocpserver &
cd $EBLOCBROKER
nohup python py_clusterDriver.py &
```

----

## Connect to eBlocBroker Contract

```bash
address="0x7618d74380dcf4db2b6f33027cf95879da60e68a";
abi=[{"constant":true,"inputs":[{"name":"index","type":"uint256"}],"name":"getQueuedCancelJob","outputs":[{"name":"","type":"string"},{"name":"","type":"uint256"}],"payable":false,"type":"function"},{"constant":true,"inputs":[{"name":"c_id","type":"address"},{"name":"ipfsHash","type":"string"},{"name":"index","type":"uint256"}],"name":"getJobInfo","outputs":[{"name":"","type":"string"},{"name":"","type":"string"},{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"uint32"},{"name":"","type":"uint32"},{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"uint256"},{"name":"","type":"uint256"}],"payable":false,"type":"function"},{"constant":true,"inputs":[],"name":"getQueuedJobSize","outputs":[{"name":"","type":"uint256"}],"payable":false,"type":"function"},{"constant":true,"inputs":[{"name":"c_id","type":"address"}],"name":"getClusterReceivedAmount","outputs":[{"name":"","type":"uint256"}],"payable":false,"type":"function"},{"constant":true,"inputs":[{"name":"c_id","type":"address"}],"name":"getClusterName","outputs":[{"name":"","type":"string"}],"payable":false,"type":"function"},{"constant":false,"inputs":[{"name":"ipfsHash","type":"string"},{"name":"index","type":"uint32"},{"name":"jobRunTimeMinute","type":"uint32"},{"name":"ipfsHashOut","type":"string"}],"name":"receiptCheck","outputs":[{"name":"success","type":"bool"}],"payable":false,"type":"function"},{"constant":false,"inputs":[{"name":"val","type":"uint256"}],"name":"setIndexReadFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"type":"function"},{"constant":true,"inputs":[{"name":"c_id","type":"address"}],"name":"getClusterCoreMinutePrice","outputs":[{"name":"","type":"uint256"}],"payable":false,"type":"function"},{"constant":false,"inputs":[],"name":"stopCluster","outputs":[{"name":"success","type":"bool"}],"payable":false,"type":"function"},{"constant":true,"inputs":[],"name":"getClusterAddresses","outputs":[{"name":"","type":"address[]"}],"payable":false,"type":"function"},{"constant":false,"inputs":[{"name":"ipfsHash","type":"string"},{"name":"index","type":"uint32"},{"name":"jobStatus","type":"string"},{"name":"jobId","type":"uint32"}],"name":"setJobStatus","outputs":[{"name":"success","type":"bool"}],"payable":false,"type":"function"},{"constant":false,"inputs":[{"name":"coreLimit","type":"uint32"},{"name":"clusterName","type":"string"},{"name":"fID","type":"string"},{"name":"price","type":"uint256"}],"name":"createCluster","outputs":[{"name":"success","type":"bool"}],"payable":false,"type":"function"},{"constant":true,"inputs":[{"name":"c_id","type":"address"}],"name":"getClusterFederationCloudId","outputs":[{"name":"","type":"string"}],"payable":false,"type":"function"},{"constant":false,"inputs":[],"name":"testCallStack","outputs":[{"name":"","type":"int256"}],"payable":false,"type":"function"},{"constant":false,"inputs":[{"name":"c_id","type":"address"},{"name":"ipfsHash","type":"string"},{"name":"index","type":"uint32"},{"name":"folderType","type":"bytes1"}],"name":"refundMe","outputs":[{"name":"","type":"bool"}],"payable":false,"type":"function"},{"constant":true,"inputs":[],"name":"getIndexReadFrom","outputs":[{"name":"","type":"uint256"}],"payable":false,"type":"function"},{"constant":true,"inputs":[{"name":"c_id","type":"address"}],"name":"getClusterCoreLimit","outputs":[{"name":"","type":"uint256"}],"payable":false,"type":"function"},{"constant":true,"inputs":[{"name":"index","type":"uint256"}],"name":"getQueuedJob","outputs":[{"name":"","type":"string"},{"name":"","type":"uint256"},{"name":"","type":"bytes1"}],"payable":false,"type":"function"},{"constant":true,"inputs":[{"name":"c_id","type":"address"},{"name":"ipfsHash","type":"string"},{"name":"index","type":"uint256"}],"name":"getSubmittedJobCore","outputs":[{"name":"","type":"uint32"}],"payable":false,"type":"function"},{"constant":true,"inputs":[{"name":"c_id","type":"address"},{"name":"ipfsHash","type":"string"}],"name":"getJobSize","outputs":[{"name":"","type":"uint256"}],"payable":false,"type":"function"},{"constant":false,"inputs":[{"name":"c_id","type":"address"},{"name":"ipfsHash","type":"string"},{"name":"core","type":"uint32"},{"name":"jobDesc","type":"string"},{"name":"coreMinuteGas","type":"uint32"},{"name":"folderType","type":"bytes1"}],"name":"insertJob","outputs":[{"name":"success","type":"bool"}],"payable":true,"type":"function"},{"constant":false,"inputs":[{"name":"c_id","type":"address"},{"name":"coreLimit","type":"uint32"},{"name":"clusterName","type":"string"},{"name":"fID","type":"string"},{"name":"price","type":"uint256"}],"name":"updateClusterInfo","outputs":[{"name":"success","type":"bool"}],"payable":false,"type":"function"},{"anonymous":false,"inputs":[{"indexed":false,"name":"cluster","type":"address"},{"indexed":false,"name":"recipient","type":"address"},{"indexed":false,"name":"hash","type":"string"},{"indexed":false,"name":"index","type":"uint256"},{"indexed":false,"name":"desc","type":"string"},{"indexed":false,"name":"requestedCore","type":"uint32"},{"indexed":false,"name":"coreMinuteGas","type":"uint32"},{"indexed":false,"name":"jobSubmittedBlk","type":"uint256"},{"indexed":false,"name":"paid","type":"uint256"}],"name":"LogJob","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"cluster","type":"address"},{"indexed":false,"name":"recipient","type":"address"},{"indexed":false,"name":"ipfsHash","type":"string"},{"indexed":false,"name":"refundAmount","type":"uint256"},{"indexed":false,"name":"receivedAmount","type":"uint256"},{"indexed":false,"name":"startTime","type":"uint256"},{"indexed":false,"name":"endTime","type":"uint256"},{"indexed":false,"name":"jobId","type":"uint32"}],"name":"LogReceipt","type":"event"}]
var eBlocBroker = web3.eth.contract(abi).at(address);
```

### Cluster Owner: How to create a cluster:

Please note that: if you don't have any `Federated Cloud ID`, give an empty string: `""`.

```bash
coreNumber         = 128;
clusterName        = "ebloc";
federationCloudId  = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu";
corePriceMinuteWei = 1000000000000000; //For experimental you could give 1.
eBlocBroker.createCluster(coreNumber, clusterName, federationCloudId, corePriceMinuteWei); 
```

**Trigger code on start and end of the submitted job:** Cluster should do: `sudo chmod +x /path/to/slurmScript.sh`. This will allow script to be readable and executable by any SlurmUser. Update following line on the slurm.conf file: `MailProg=/home/ubuntu/eBlocBroker/slurmScript.sh`

```bash
cd $EBLOCBROKER
sudo chmod 775 endCodeAnalyse/
sudo chmod 775 transactions/
sudo chmod 775 ipfs_hashes/
```

-----

### Client Side: How to submit a Job with IPFS Hash:

Is is important that first you should run IPFS daemon on the background: `ipfs daemon &`. If it is not running, cluster is not able to get the IPFS object from the client's node.

If IPFS is successfully running on the background you should see something like this:

```bash
[~]$ ps aux | grep 'ipfs daemon' | grep -v 'grep'
avatar           24190   1.1  2.1 556620660 344784 s013  SN    3:59PM   4:10.74 ipfs daemon
```

`mkdir ipfs_codes && cd ipfs_codes`

Create `helloworld.cpp`:

```bash
#include <iostream>
#include <fstream>
using namespace std;

int main () {
  ofstream myfile;
  myfile.open ("helloworld.txt");
  myfile << "Hello World.\n";
  myfile.close();
  return 0;
}
```

Client should put his SLURM script inside a file called `run.sh`. Please note that you do not have to identify `-n` and `-t` parameters, since they will be overritten with arguments provided by the client on the cluster side.

**For example:** 

Create `run.sh`:

```bash
#!/bin/bash
#SBATCH -o slurm.out        # STDOUT
#SBATCH -e slurm.err        # STDERR
#SBATCH --mail-type=ALL
#SBATCH --mail-user=alper.alimoglu@gmail.com 
#SBATCH --requeue

g++ helloworld.cpp -o hello
./hello
sleep 60;
```

Target into the folder you want to submit and please do: `ipfs add -r .` You will face something similiar with following output:

```bash
added QmYsUBd5F8FA1vcUsMAHCGrN8Z92TdpNBAw6rMxWwmQeMJ ipfs_code/helloworld.cpp
added QmbTzBprmFEABAWwmw1VojGLMf3nv7Z16eSgec55DYdbiX ipfs_code/run.sh
added QmXsCmg5jZDvQBYWtnAsz7rukowKJP3uuDuxfS8yXvDb8B ipfs_code
```
Main folder's IPFS hash(for example:`QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vd`) would be used as key to the submitted job to the `eBlocBroker` by the client.

**How To Submit Job:** 

```bash
eBlocBroker.getClusterAddresses(); //returns all available Clusters Addresses.
["0x6af0204187a93710317542d383a1b547fa42e705"]
```
###**Submit IPFS folder :**

```bash
clusterID      = "0x6af0204187a93710317542d383a1b547fa42e705"; //clusterID you would like to submit.
pricePerMin    = eBlocBroker.getClusterCoreMinutePrice(clusterID);

jobHash        = "QmefdYEriRiSbeVqGvLx15DKh4WqSMVL8nT4BwvsgVZ7a5"
coreNum        = 1; //Before assigning this value please check the coreLimit of the cluster.
coreGasDay     = 0;
coreGasHour    = 0;
coreGasMin     = 10;
jobDescription = "Science"
coreMinuteGas  = coreGasMin + coreGasHour * 60 + coreGasDay * 1440;
folderType     = '0' ; // Please note that '0' stands for IPFS , '1' stands for eudat.

clusterCoreLimit = eBlocBroker.getClusterCoreLimit(clusterID) ;
if (coreNum <= clusterCoreLimit ) {
	//Following line submits the Job:
	eBlocBroker.insertJob(clusterID, jobHash, coreNum, jobDescription, coreMinuteGas, folderType, {from: web3.eth.accounts[0], value: coreNum*pricePerMin*coreMinuteGas, gas: 3000000 } );
}
```

###**Submit eudat folder :**

Before doing this you have to be sure that you have shared your folder with cluster's FId. Please follow ...<github issue>. Otherwise your job will not accepted.


Now `jobHash` should be your `FederationCloudId` followed by the name of the folder your are sharing having equal symbol in between.

Example:
`jobHash="3d8e2dc2-b855-1036-807f-9dbd8c6b1579=folderName"`


```bash
clusterID      = "0x6af0204187a93710317542d383a1b547fa42e705"; //clusterID you would like to submit.
pricePerMin    = eBlocBroker.getClusterCoreMinutePrice(clusterID);
jobHash        = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579=folderName"
coreNum        = 1; //Before assigning this value please check the coreLimit of the cluster.
coreGasDay     = 0;
coreGasHour    = 0;
coreGasMin     = 10;
jobDescription = "Science"
coreMinuteGas  = coreGasMin + coreGasHour * 60 + coreGasDay * 1440;
folderType     = '1' ; // Please note that '0' stands for IPFS , '1' stands for eudat.

clusterCoreLimit = eBlocBroker.getClusterCoreLimit(clusterID) ;
if (coreNum <= clusterCoreLimit ) {
	//Following line submits the Job:
	eBlocBroker.insertJob(clusterID, jobHash, coreNum, jobDescription, coreMinuteGas, folderType, {from: web3.eth.accounts[0], value: coreNum*pricePerMin*coreMinuteGas, gas: 3000000 } );
}
```



**Obtain Submitted Job's Information:**

This will return:

- status  == `"QUEUED"` or `"RUNNING"` or `"COMPLETED"` 
- ipfsOut == Completed Job's resulted folder. This exists if the job is completed.
- jobId,  //on the Slurm side.
- coreMinuteGas,
- jobSubmittedBlockNumber, 
- jobStartedTimeStamp
- jobEndedimeStamp


```bash
clusterID="0x6af0204187a93710317542d383a1b547fa42e705"; //clusterID that you have submitted your job.
index   = 0;      
jobHash = "QmXsCmg5jZDvQBYWtnAsz7rukowKJP3uuDuxfS8yXvDb8B"
eBlocBroker.getJobInfo(clusterID, jobHash, 0);
```

**Obtain Cluster Information:**

```bash
eBlocBroker.getClusterReceivedAmount(clusterID) //Learn amount gained by the Cluster.
eBlocBroker.getClusterCoreLimit(clusterID)
eBlocBroker.getClusterFederationCloudId(clusterID)
```

If same hash job submitted more than one time do following to get all information:

```bash
for(var i = 0; i < eBlocBroker.getJobSize(clusterID, jobHash); i++){
	console.log( eBlocBroker.getJobInfo(clusterID, jobHash, i) );
}
```

**Events: In order to keep track of the log of receipts**

```bash
fromBlock = MyContract.eth.blockNumber; //This could be also the blockNumber the job submitted.
var e = myContractInstance.LogReceipt({}, {fromBlock:fromBlock, toBlock:'latest'});
e.watch(function(error, result){
  console.log(JSON.stringify(result));
});
```