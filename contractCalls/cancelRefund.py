#!/usr/bin/env python

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
sys.path.insert(1, os.path.join(sys.path[0], '..')); import constants
os.chdir(sys.path[0]);

# checks: does IPFS run on the background or not
def isIpfsOn():
   check = os.popen("ps aux | grep \'[i]pfs daemon\' | wc -l").read().rstrip('\n');
   if int(check) == 0:
      print("Error: IPFS does not work on the background.\nPlease run:  ipfs daemon &");
      os.system("bash ../runIPFS.sh");
      time.sleep(5);
      os.system("cat ipfs.out");      
      
# Note that you should create only one RPCProvider per process,
# as it recycles underlying TCP/IP network connections between
# your process and Ethereum node
web3 = Web3(HTTPProvider('http://localhost:' + str(constants.RPC_PORT)))

if not web3.isConnected():
    print('notconnected')
    sys.exit()

fileAddr        = open("address.json", "r")
contractAddress = fileAddr.read().replace("\n", "")

with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)
   
contractAddress = web3.toChecksumAddress(contractAddress);    
eBlocBroker     = web3.eth.contract(contractAddress, abi=abi);

if __name__ == '__main__': #{
    if(len(sys.argv) == 10): #{
        clusterAddress = web3.toChecksumAddress(str(sys.argv[1]));
        blockReadFrom, coreNumber, pricePerMin = eBlocBroker.call().getClusterInfo(clusterAddress);
        my_filter = eBlocBroker.eventFilter('LogCluster',{'fromBlock':int(blockReadFrom),'toBlock':int(blockReadFrom) + 1})
        jobKey         = str(sys.argv[2]);
        coreNum        = int(sys.argv[3]);
        coreGasDay     = int(sys.argv[4]);
        coreGasHour    = int(sys.argv[5]);
        coreGasMin     = int(sys.argv[6]);
        jobDescription = str(sys.argv[7]);
        storageType    = int(sys.argv[8]);
        accountID      = int(sys.argv[9]);
    #}
    else: #{
        # USER Inputs ================================================================
        clusterAddress = web3.toChecksumAddress("0x75a4c787c5c18c587b284a904165ff06a269b48c");    
        jobKey         = "QmRsaBEGcqxQcJbBxCi1LN9iz5bDAGDWR6Hx7ZvWqgqmdR"; # Long Sleep Job.
        index          = 1;
        accountID      = 0;
        # =============================================================================
    #}

    if not eBlocBroker.functions.isClusterExist(clusterAddress).call(): #{
       print("Requested cluster's Ethereum Address (" + clusterAddress + ") does not exist.")
       sys.exit();
    #}
    
    fromAccount = web3.eth.accounts[accountID];
    fromAccount = web3.toChecksumAddress(fromAccount);
    if not eBlocBroker.functions.isUserExist(fromAccount).call(): #{
       print("Requested user's Ethereum Address (" + fromAccount + ") does not exist.")
       sys.exit();
    #}
      
    tx = eBlocBroker.transact({"from": web3.eth.accounts[accountID], "gas": 4500000}).cancelRefund(clusterAddress, jobKey, index);
    print('Tx: ' + tx.hex());
#}
