#!/usr/bin/env python3

import sys, os, json
from imports import connectEblocBroker, getWeb3
from os.path import expanduser
home = expanduser("~")
    
def updateProvider():
    web3        = getWeb3() 
    eBlocBroker = connectEblocBroker(web3)
    # USER Inputs----------------------------------------------------------------
    # account            = web3.eth.accounts[0]  # Provider's Ethereum Address
    PROVIDER_ID         = web3.toChecksumAddress(os.getenv("PROVIDER_ID"))  
    availableCoreNum   = 128 
    email              = "alper01234alper@gmail.com"
    federationCloudId  = "5f0db7e4-3078-4988-8fa5-f066984a8a97@b2drop.eudat.eu" 
    miniLockId         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ" 
    priceCoreMin       = 100
    priceDataTransfer  = 10
    priceStorage       = 10
    priceCache         = 10
    ipfsAddress        = "/ip4/193.140.196.159/tcp/4001/ipfs/QmNQ74xaWquZseMhZJCPfV47WttP9hAoPEXeCMKsh3Cap4"
    # ----------------------------------------------------------------------------
    #os.environ['ipfs'] = ipfs 
    #ipfsID=os.popen('node bs58.js encode $ipfs').read().replace("\n", "") 
    #ipfsIDbytes = web3.toBytes(hexstr=ipfsID)
    if not os.path.isfile(home + '/.eBlocBroker/whisperInfo.txt'):
		# First time running:
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

    if len(federationCloudId) < 128 and len(email) < 128 and (len(miniLockId) == 0 or len(miniLockId) == 45):
        tx_hash = eBlocBroker.transact({"from": PROVIDER_ID,
                                        "gas": 4500000}).updateProvider(email,
                                                                         federationCloudId,
                                                                         miniLockId,
                                                                         availableCoreNum,
                                                                         priceCoreMin,
                                                                         priceDataTransfer,
                                                                         priceStorage,
                                                                         priceCache,
                                                                         ipfsAddress,
                                                                         whisperPubKey) 
        print('Tx_hash: ' + tx_hash.hex()) 
        
if __name__ == '__main__':
    updateProvider()
