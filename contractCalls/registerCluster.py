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
# USER Inputs----------------------------------------------------------------
account            = web3.eth.accounts[0]; # Cluster's Ethereum Address
coreNumber         = 4;
clusterName        = "eBlocCluster";
federationCloudId  = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu";
miniLockId         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ";
corePriceMinuteWei = 100;
ipfsAddress        = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf";
# ----------------------------------------------------------------------------
#os.environ['ipfs'] = ipfs;
#ipfsID=os.popen('node bs58.js encode $ipfs').read().replace("\n", "");
#ipfsIDbytes = web3.toBytes(hexstr=ipfsID);

if(len(federationCloudId) < 128 and len(clusterName) < 32 and (len(miniLockId) == 0 or len(miniLockId) == 45)): #{
    tx = eBlocBroker.transact({"from":account, "gas": 4500000}).registerCluster(coreNumber, clusterName, federationCloudId, miniLockId, corePriceMinuteWei, ipfsAddress);
    print('Tx: ' + tx.hex());
#}
