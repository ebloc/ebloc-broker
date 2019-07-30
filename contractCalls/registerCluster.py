#!/usr/bin/env python3

import os, sys,json
from dotenv  import load_dotenv
from imports import connectEblocBroker, getWeb3
from contractCalls.isClusterExists import isClusterExists
from os.path import expanduser
home = expanduser("~")
load_dotenv(os.path.join(home + '/.eBlocBroker/', '.env')) # Load .env from the given path
   
web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)
CLUSTER_ID  = web3.toChecksumAddress(os.getenv('CLUSTER_ID'))

def registerCluster(availableCoreNum, clusterEmail, federationCloudId, miniLockId, priceCoreMin, priceDataTransfer, priceStorage,
                    priceCache, ipfsAddress, commitmentBlockNum):
    account = CLUSTER_ID # The Ethereum Address that cluster want to register
    if not os.path.isfile(home + '/.eBlocBroker/whisperInfo.txt'):
        print('Please first run: ../scripts/whisperInitialize.py')
        sys.exit()
    else:
        with open(home + '/.eBlocBroker/whisperInfo.txt') as json_file:
            data = json.load(json_file)
            kId = data['kId']
            whisperPubKey = data['publicKey']
            
        if not web3.shh.hasKeyPair(kId):
            print("Whisper node's private key of a key pair did not match with the given ID.")
            print('Please re-run: ../scripts/whisperInitialize.py')
            sys.exit()
    
    if isClusterExists(account):
        print('Cluster is already registered. Please call the updateCluster() function.')
        sys.exit()
    
    if len(federationCloudId) < 128 and len(clusterEmail) < 128 and (len(miniLockId) == 0 or len(miniLockId) == 45):
        tx_hash = eBlocBroker.transact({"from":account, "gas": 4500000}).registerCluster(clusterEmail, federationCloudId,
                                                                                         miniLockId,
                                                                                         availableCoreNum,
                                                                                         priceCoreMin,
                                                                                         priceDataTransfer,
                                                                                         priceStorage,
                                                                                         priceCache,
                                                                                         commitmentBlockNum,
                                                                                         ipfsAddress,
                                                                                         whisperPubKey) 
        print('Tx_hash: ' + tx_hash.hex()) 

if __name__ == '__main__':
    availableCoreNum   = 128 
    clusterEmail       = "alper01234alper@gmail.com" 
    federationCloudId  = "5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu" 
    miniLockId         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ" 
    priceCoreMin       = 100
    priceDataTransfer  = 10
    priceStorage       = 10
    priceCache         = 10
    commitmentBlockNum = 10
    ipfsAddress        = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"

    registerCluster(availableCoreNum, clusterEmail, federationCloudId, miniLockId, priceCoreMin, priceDataTransfer, priceStorage, priceCache, ipfsAddress, commitmentBlockNum)
    

    # os.environ['ipfs'] = ipfs 
    # ipfsID=os.popen('node bs58.js encode $ipfs').read().replace("\n", "") 
    # ipfsIDbytes = web3.toBytes(hexstr=ipfsID)     
