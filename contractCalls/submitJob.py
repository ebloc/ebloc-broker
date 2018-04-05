#!/usr/bin/env python

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
sys.path.insert(1, os.path.join(sys.path[0], '..')); import constants
os.chdir(sys.path[0]);

# checks: does IPFS run on the background or not
def isIpfsOn():
   check = os.popen("ps aux | grep \'[i]pfs daemon\' | wc -l").read().rstrip('\n');
   if (int(check) == 0):
      print("Error: IPFS does not work on the background.\nPlease run:  ipfs daemon &");
      os.system("bash ../runIPFS.sh");
      time.sleep(5);
      os.system("cat ipfs.out");      
   else:
      print("IPFS is already on");
      
   os.popen("ipfs swarm connect");   
   # Do swarm connect!
      
# Note that you should create only one RPCProvider per process,
# as it recycles underlying TCP/IP network connections between
# your process and Ethereum node
web3 = Web3(HTTPProvider('http://localhost:' + str(constants.RPC_PORT)))

fileAddr        = open("address.json", "r")
contractAddress = fileAddr.read().replace("\n", "")

with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)
   
contractAddress = web3.toChecksumAddress(contractAddress);    
eBlocBroker     = web3.eth.contract(contractAddress, abi=abi);

if __name__ == '__main__': #{
    if(len(sys.argv) == 11):
        clusterAddress = str(sys.argv[1]);
        blockReadFrom, coreNumber, pricePerMin = eBlocBroker.call().getClusterInfo(clusterAddress);       
        jobKey         = str(sys.argv[2]);
        coreNum        = int(sys.argv[3]);
        coreGasDay     = int(sys.argv[4]);
        coreGasHour    = int(sys.argv[5]);
        coreGasMin     = int(sys.argv[6]);
        jobDescription = str(sys.argv[7]);
        storageType    = int(sys.argv[8]);
        myMiniLockId   = str(sys.argv[9]);
        accountID      = int(sys.argv[10]);
    else:
        # USER Inputs----------------------------------------------------------------
        clusterAddress = "0x6af0204187a93710317542d383a1b547fa42e705";
        clusterAddress = web3.toChecksumAddress(clusterAddress);    
        blockReadFrom, coreNumber, pricePerMin = eBlocBroker.functions.getClusterInfo(clusterAddress).call();
        
        jobKey         = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579=folderName";
        coreNum        = 1;
        coreGasDay     = 0;
        coreGasHour    = 0;
        coreGasMin     = 1;
        jobDescription = "Science";
        storageType    = 1;
        myMiniLockId   = "";
        accountID      = 0;
        # ----------------------------------------------------------------------------
    if storageType == 0 or storageType == 2:
       isIpfsOn();

    coreMinuteGas = coreGasMin + coreGasHour * 60 + coreGasDay * 1440;
    msgValue      = coreNum * pricePerMin * coreMinuteGas;

    if (not eBlocBroker.functions.isClusterExist(clusterAddress).call()):
       print("Requested Cluster's Ethereum Address does not exist.")
       sys.exit();

    if (storageType == 0 and len(jobKey) != 46) or (storageType == 2 and len(jobKey) != 46):
       print("IPFS Hash's length does not match with original length.")
       sys.exit();

    #if storageType == 0 or storageType == 2:
    #       isIpfsOn();

    gas_price = web3.eth.gasPrice * 2;
    nonce = web3.eth.getTransactionCount(web3.eth.accounts[accountID])
    
    gasLimit=3000000; 
    if (coreNum <= coreNumber and len(jobDescription) < 128):
       tx = eBlocBroker.transact({"from": web3.eth.accounts[accountID], "value": msgValue, "gas": gasLimit}).submitJob(clusterAddress, jobKey, coreNum, jobDescription, coreMinuteGas, storageType, myMiniLockId);
       print('Tx: ' + tx.hex());
#}


