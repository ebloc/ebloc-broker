#!/usr/bin/env python3

import os, json, sys, time
from web3 import Web3
from web3.providers.rpc import HTTPProvider
sys.path.insert(1, os.path.join(sys.path[0], '..'))
import lib
os.chdir(sys.path[0])

# Note that you should create only one RPCProvider per process,
# as it recycles underlying TCP/IP network connections between
# your process and Ethereum node
web3 = Web3(HTTPProvider('http://localhost:' + str(constants.RPC_PORT)))

fileAddr = open("address.json", "r")
contractAddress = fileAddr.read().replace("\n", "")

with open('abi.json', 'r') as abi_definition:
    abi = json.load(abi_definition)

contractAddress = web3.toChecksumAddress(contractAddress)    
eBlocBroker = web3.eth.contract(contractAddress, abi=abi)
# USER Inputs----------------------------------------------------------------


# eBloc-NAS
account            = web3.eth.accounts[0] # Cluster's Ethereum Address
coreNumber         = 2
clusterEmail       = "alper.alimoglu@gmail.com"
federationCloudId  = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
miniLockId         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
corePriceMinuteWei = 100
ipfsAddress        = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"


# TETAM
account            = web3.eth.accounts[0] # Cluster's Ethereum Address
coreNumber         = 128
clusterEmail       = "alper01234alper@gmail.com"
federationCloudId  = ""
miniLockId         = ""
corePriceMinuteWei = 100
ipfsAddress        = "/ip4/193.140.196.159/tcp/4001/ipfs/QmNQ74xaWquZseMhZJCPfV47WttP9hAoPEXeCMKsh3Cap4"


# Google-Drive Instance-1
account            = web3.eth.accounts[0] # Cluster's Ethereum Address
coreNumber         = 64
clusterEmail       = ""
federationCloudId  = ""
miniLockId         = ""
corePriceMinuteWei = 100
ipfsAddress        = "/ip4/34.73.108.63/tcp/4001/ipfs/QmXqUW6n57c2e4Y6461CiNkdSuYEGtnNYrWHCVeNEcW3Td"

# Google-Drive Instance-2
account            = web3.eth.accounts[0] # Cluster's Ethereum Address
coreNumber         = 64
clusterEmail       = ""
federationCloudId  = ""
miniLockId         = "SjPmN3Fet4bKSBJAutnAwA15ct9UciNBNYo1BQCFiEjHn"
corePriceMinuteWei = 100
ipfsAddress        = ""





# =======================================================================================================
# AWS-IPFS
account            = web3.eth.accounts[0] # Cluster's Ethereum Address
coreNumber         = 64
clusterEmail       = ""
federationCloudId  = ""
miniLockId         = ""
corePriceMinuteWei = 100
ipfsAddress        = "/ip4/54.145.188.102/tcp/4001/ipfs/QmTkEBxqiX68P9ByBk5f4b58Dg2vyEFf9Cc6FPL8SskbJx"

# AWS-IPFS_miniLock
account            = web3.eth.accounts[0] # Cluster's Ethereum Address
coreNumber         = 64
clusterEmail       = ""
federationCloudId  = ""
miniLockId         = "yWfGR7GEdfw5kphyZYcs3smvx2MmBoQdBE6hAxTv5d3ZV"
corePriceMinuteWei = 100
ipfsAddress        = "/ip4/174.129.113.214/tcp/4001/ipfs/QmTDHH9n8qbaeuwjsDuBzUu2DySNay2TNL8v9WeiBtNjge"



# ----------------------------------------------------------------------------

if len(federationCloudId) < 128 and len(clusterEmail) < 128 and (len(miniLockId) == 0 or len(miniLockId) == 45):
    tx = eBlocBroker.transact({"from":account, "gas": 4500000}).registerCluster(coreNumber, clusterEmail, federationCloudId, miniLockId, corePriceMinuteWei, ipfsAddress)
    print('Tx: ' + tx.hex())
