#!/usr/bin/env python3

import os, sys,json
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from imports import connectEblocBroker
from imports import getWeb3
from os.path import expanduser
home = expanduser("~")

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)

if __name__ == '__main__':
    # USER Inputs----------------------------------------------------------------
    account           = web3.eth.accounts[0]  # Cluster's Ethereum Address
    coreNumber        = 2 
    clusterEmail      = "alper.alimoglu@gmail.com" 
    federationCloudId = "5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu" 
    miniLockId        = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ" 
    priceCoreMin      = 100
    priceDataTransfer    = 10
    ipfsAddress       = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"
    # whisperPubKey     = "0x04aec8867369cd4b38ce7c212a6de9b3aceac4303d05e54d0da5991194c1e28d36361e4859b64eaad1f95951d2168e53d46f3620b1d4d2913dbf306437c62683a6"
    # ----------------------------------------------------------------------------	
    if not os.path.isfile(home + '/.eBlocBroker/whisperInfo.txt'):
		# First time running:
        log('Please first run: python whisperInitialize.py')
        sys.exit()
    else:
        with open(home + '/.eBlocBroker/whisperInfo.txt') as json_file:
            data = json.load(json_file)
            kId = data['kId']
            whisperPubKey = data['publicKey']
        if not web3.shh.hasKeyPair(kId):
            log("Whisper node's private key of a key pair did not match with the given ID")
            sys.exit()

    if len(federationCloudId) < 128 and len(clusterEmail) < 128 and (len(miniLockId) == 0 or len(miniLockId) == 45):
        tx_hash = eBlocBroker.transact({"from":account, "gas": 4500000}).registerCluster(coreNumber, clusterEmail, federationCloudId, miniLockId, priceCoreMin, priceDataTransfer, ipfsAddress, whisperPubKey) 
        print('Tx_hash: ' + tx_hash.hex()) 

    # os.environ['ipfs'] = ipfs 
    # ipfsID=os.popen('node bs58.js encode $ipfs').read().replace("\n", "") 
    # ipfsIDbytes = web3.toBytes(hexstr=ipfsID)     
