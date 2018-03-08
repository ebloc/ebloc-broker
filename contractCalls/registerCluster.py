#!/usr/bin/env python

import os
from web3 import Web3
import json
from web3.providers.rpc import HTTPProvider

# Note that you should create only one RPCProvider per process,
# as it recycles underlying TCP/IP network connections between
# your process and Ethereum node
web3 = Web3(HTTPProvider('http://localhost:8545'))

contractAddress='0xca9f407af4e36bfd4546a898d06c51cdc0da8a2a';
with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)
    
eBlocBroker = web3.eth.contract(contractAddress, abi=abi);
# USER Inputs----------------------------------------------------------------
coreNumber         = 128;
clusterName        = "eBlocCluster";
federationCloudId  = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu";
miniLockId         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ";
corePriceMinuteWei = 100;
ipfs               = "QmWmyoMoctfbAaiEs2G46gpeUmhqFRDW6KWo64y5r581Vz";
# ----------------------------------------------------------------------------

os.environ['ipfs'] = ipfs;
ipfsID=os.popen('node bs58.js encode $ipfs').read().replace("\n", "");

ipfsIDbytes = web3.toBytes(hexstr=ipfsID);
account     = web3.eth.accounts[7];

if(len(federationCloudId) < 128 and len(clusterName) < 32 and (len(miniLockId) == 0 or len(miniLockId) == 45)):
    tx=eBlocBroker.transact({"from":account}).registerCluster(coreNumber, clusterName, federationCloudId, miniLockId, corePriceMinuteWei, ipfsIDbytes);
    print(tx);
