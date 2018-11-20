#!/usr/bin/env python3

import os, sys, json
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from imports import connectEblocBroker
from imports import getWeb3
from contractCalls.isUserExist import isUserExist
from os.path import expanduser
home = expanduser("~")

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)

def registerUser(accountID, userEmail, federationCloudID, miniLockID, ipfsAddress, orcID, githubUserName, eBlocBroker=None, web3=None): 
	if eBlocBroker == None and web3 == None: 
		sys.path.insert(1, os.path.join(sys.path[0], '..'))
		from imports import connectEblocBroker
		from imports import getWeb3
		web3           = getWeb3()
		eBlocBroker    = connectEblocBroker(web3)

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
	account = web3.eth.accounts[int(accountID)]  # User's Ethereum Address

	if isUserExist(account, eBlocBroker, web3):
		return 'User (' + account  + ') is already registered.'
    
	if len(federationCloudID) < 128 and len(userEmail) < 128 and len(orcID) == 19 and orcID.replace("-", "").isdigit(): 
		tx = eBlocBroker.transact({"from":account, "gas": 4500000}).registerUser(userEmail, federationCloudID, miniLockID, ipfsAddress,
                                                                                 orcID, githubUserName, whisperPubKey) 
		return  'Tx_hash: ' + tx.hex()

if __name__ == '__main__': 
    if len(sys.argv) == 8:
        account            = int(sys.argv[1])
        userEmail          = str(sys.argv[2]) 
        federationCloudID  = str(sys.argv[3]) 
        miniLockID         = str(sys.argv[4]) 
        ipfsAddress        = str(sys.argv[5]) 
        orcID              = str(sys.argv[6]) 
        githubUserName     = str(sys.argv[7]) 
    else:
        account            = 0  # User's Ethereum Address
        userEmail          = "alper01234alper@gmail.com" # "alper.alimoglu@gmail.com" 
        federationCloudID  = "059ab6ba-4030-48bb-b81b-12115f531296" 
        miniLockID         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ" 
        ipfsAddress        = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf" 
        orcID              = "0000-0001-7642-0552" 
        githubUserName     = "eBloc"

    res = registerUser(account, userEmail, federationCloudID, miniLockID, ipfsAddress, orcID, githubUserName)
    print(res)
