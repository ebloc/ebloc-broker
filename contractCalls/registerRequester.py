#!/usr/bin/env python3

import os, sys, json, pprint
from os.path import expanduser
from isRequesterExists import isRequesterExists
from imports import connect, getWeb3
home = expanduser("~")

def registerRequester(accountID, email, federationCloudID, miniLockID, ipfsAddress, githubUsername, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return

    if not os.path.isfile(home + '/.eBlocBroker/whisperInfo.txt'):
        return False, 'Please first run: python ~/eBlocBroker/scripts/whisperInitialize.py'
    else:
        with open(home + '/.eBlocBroker/whisperInfo.txt') as jsonFile:
            data = json.load(jsonFile)
            kId = data['kId']
            whisperPubKey = data['publicKey']
            
        if not w3.geth.shh.hasKeyPair(kId):
            return False, "Whisper node's private key of a key pair did not match with the given ID"
            
    account = w3.eth.accounts[int(accountID)] # Requester's Ethereum Address

    if isRequesterExists(account, eBlocBroker, w3):
        return False, 'Requester "' + account  + '" is already registered.'
    
    if len(federationCloudID) < 128 and len(email) < 128:
        try:
            tx = eBlocBroker.functions.registerRequester(email, federationCloudID, miniLockID, ipfsAddress, githubUsername, whisperPubKey).transact({"from":account, "gas": 4500000})
        except Exception:
            return False, traceback.format_exc()
        
        return True, tx.hex()

if __name__ == '__main__': 
    if len(sys.argv) == 7:
        account            = int(sys.argv[1])
        email              = str(sys.argv[2]) 
        federationCloudID  = str(sys.argv[3]) 
        miniLockID         = str(sys.argv[4]) 
        ipfsAddress        = str(sys.argv[5]) 
        githubUsername     = str(sys.argv[6]) 
    else:
        account            = 0  # Requster's Ethereum Address
        email              = "alper01234alper@gmail.com" # "alper.alimoglu@gmail.com" 
        federationCloudID  = "059ab6ba-4030-48bb-b81b-12115f531296" 
        miniLockID         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ" 
        ipfsAddress        = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf" 
        githubUsername     = "eBloc"
        
    w3 = getWeb3()
    status, result = registerRequester(account, email, federationCloudID, miniLockID, ipfsAddress, githubUsername, None, w3)
    if status:
        print('tx_hash: ' + result)        
        receipt = w3.eth.waitForTransactionReceipt(result)
        print("Transaction receipt mined: \n")
        pprint.pprint(dict(receipt))
        print("Was transaction successful?")
        pprint.pprint(receipt['status'])        
    else:
        print(result)

