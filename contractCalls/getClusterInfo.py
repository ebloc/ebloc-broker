#!/usr/bin/env python -W ignore::DeprecationWarning

from __future__ import print_function
import os, sys
from web3 import Web3
import json
from web3.providers.rpc import HTTPProvider


os.chdir(sys.path[0]);

'''
def ipfsBytesToString(ipfsID):
    val= web3.fromAscii(ipfsID);
    os.environ['val'] = '1220'+val[2:];
    return os.popen('node bs58.js decode $val').read().replace("\n", "");
'''

web3 = Web3(HTTPProvider('http://localhost:8545'))

fileAddr = open("address.json", "r")
contractAddress = fileAddr.read().replace("\n", "")

with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)
    
eBlocBroker = web3.eth.contract(contractAddress, abi=abi);

if __name__ == '__main__': #{
    if(len(sys.argv) == 2):
        clusterAddress = str(sys.argv[1]);
    else:
        clusterAddress = "0xc75497b304f42631d919f20db3e9b79dd59e88ff";
        
    if (str(eBlocBroker.call().isClusterExist(clusterAddress)) == "False"):
        print("Cluster is not registered")
        sys.exit();

    blockReadFrom, coreNumber, coreMinutePrice = eBlocBroker.call().getClusterInfo(clusterAddress);

    # ipfs=ipfsBytesToString(ipfsID)

    #print('name: ' + name);
    #print('ipfsID: ' + ipfs)
    #print('federationCloudId: ' + federationCloudId)
    #print('miniLockId: ' + miniLockId)

    print('blockReadFrom: '      + str(blockReadFrom))
    print('coreNumber: '      + str(coreNumber))
    print('coreMinutePrice: ' + str(coreMinutePrice))

    #transfer_filter = eBlocBroker.on('LogCluster', {'filter': {'_from': '0x6af0204187a93710317542d383a1b547fa42e705'}})
#}
