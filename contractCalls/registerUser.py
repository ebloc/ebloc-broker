#!/usr/bin/env python

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
sys.path.insert(1, os.path.join(sys.path[0], '..')); import constants
os.chdir(sys.path[0]);

# Note that you should create only one RPCProvider per process,
# as it recycles underlying TCP/IP network connections between
# your process and Ethereum node
web3 = Web3(HTTPProvider('http://localhost:' + str(constants.RPC_PORT)))

fileAddr = open("address.json", "r")
contractAddress = fileAddr.read().replace("\n", "")

with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)

contractAddress = web3.toChecksumAddress(contractAddress);    
eBlocBroker = web3.eth.contract(contractAddress, abi=abi);

if __name__ == '__main__': #{
    # USER Inputs----------------------------------------------------------------
    account            = web3.eth.accounts[0]; # User's Ethereum Address

    userEmail          = "alper.alimoglu@gmail.com";
    federationCloudId  = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579";
    miniLockID         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ";
    ipfsAddress        = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf";
    # ----------------------------------------------------------------------------
    
    if len(federationCloudId) < 128 and len(userEmail) < 128: #{
        tx = eBlocBroker.transact({"from":account, "gas": 4500000}).registerUser(userEmail, federationCloudId, miniLockID, ipfsAddress);
        print('Tx: ' + tx.hex());
#}
