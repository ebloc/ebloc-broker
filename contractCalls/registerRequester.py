#!/usr/bin/env python3

import os, sys, json
from os.path     import expanduser
from isRequesterExists import isRequesterExists
home = expanduser("~")

def registerRequester(accountID, email, federationCloudID, miniLockID, ipfsAddress, githubUsername, eBlocBroker=None, web3=None): 
	if eBlocBroker is None and web3 is None: 
		from imports import connectEblocBroker, getWeb3
		web3           = getWeb3()
		eBlocBroker    = connectEblocBroker(web3)

	if not os.path.isfile(home + '/.eBlocBroker/whisperInfo.txt'):
		# First time running:
		print('Please first run: python ~/eBlocBroker/scripts/whisperInitialize.py')
		sys.exit()
	else:
		with open(home + '/.eBlocBroker/whisperInfo.txt') as json_file:
			data = json.load(json_file)
			kId = data['kId']
			whisperPubKey = data['publicKey']
		if not web3.shh.hasKeyPair(kId):
			print("Whisper node's private key of a key pair did not match with the given ID")
			sys.exit()
	account = web3.eth.accounts[int(accountID)]  # Requester's Ethereum Address

	if isRequesterExists(account, eBlocBroker, web3):
		return 'Requester (' + account  + ') is already registered.'
    
	if len(federationCloudID) < 128 and len(email) < 128: 
		tx_hash = eBlocBroker.transact({"from":account, "gas": 4500000}).registerRequester(email, federationCloudID,
                                                                                 miniLockID, ipfsAddress,
                                                                                 githubUsername, whisperPubKey) 
		return  'Tx_hash: ' + tx_hash.hex()

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

    res = registerRequester(account, email, federationCloudID, miniLockID, ipfsAddress, githubUsername)
    print(res)
