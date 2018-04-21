#!/usr/bin/env python

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
sys.path.insert(1, os.path.join(sys.path[0], '..')); import constants
os.chdir(sys.path[0]);

web3 = Web3(HTTPProvider('http://localhost:' + str(constants.RPC_PORT)))

fileAddr = open("address.json", "r")
contractAddress = fileAddr.read().replace("\n", "")

with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)

contractAddress = web3.toChecksumAddress(contractAddress);
eBlocBroker = web3.eth.contract(contractAddress, abi=abi);

if __name__ == '__main__': #{
    if len(sys.argv) == 2:
        userAddress = str(sys.argv[1]);
        printType   = str(sys.argv[2]);
    else:
        userAddress = "0x82f0d257a9832fa1381881b8dce2d2e6aebc8251";
        printType   = '0';

    userAddress = web3.toChecksumAddress(userAddress);
    
    if (str(eBlocBroker.functions.isUserExist(userAddress).call()) == "False"):
        print("User is not registered. Please try again with registered Ethereum Address as user.")
        sys.exit();

    blockReadFrom = eBlocBroker.functions.getUserInfo(userAddress).call();

    my_filter = eBlocBroker.eventFilter('LogUser',{'fromBlock':int(blockReadFrom),'toBlock':int(blockReadFrom) + 1})
    # my_filter = eBlocBroker.eventFilter('LogUser',{'fromBlock':int(blockReadFrom + 1),'toBlock':int(blockReadFrom)})

    
    if printType == '0':
        print('{0: <17}'.format('blockReadFrom: ') + str(blockReadFrom))    
        print('{0: <17}'.format('userEmail: ')     + my_filter.get_all_entries()[0].args['userEmail'])
        print('{0: <17}'.format('miniLockID: ')    + my_filter.get_all_entries()[0].args['miniLockID'])
        print('{0: <17}'.format('ipfsAddress: ')   + my_filter.get_all_entries()[0].args['ipfsAddress'])   
        print('{0: <17}'.format('fID: ')           + my_filter.get_all_entries()[0].args['fID'])
    else:
        print(str(blockReadFrom) + ',' +
              my_filter.get_all_entries()[0].args['userEmail']   + ',' +
              my_filter.get_all_entries()[0].args['miniLockID']  + ',' +
              my_filter.get_all_entries()[0].args['ipfsAddress'] + ',' +
              my_filter.get_all_entries()[0].args['fID']
        );
#}
