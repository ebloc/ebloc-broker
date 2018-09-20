#!/usr/bin/env python

import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from imports import connectEblocBroker
from imports import getWeb3
from contractCalls.isUserExist import isUserExist

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)

def registerUser(accountID, userEmail, federationCloudID, miniLockID, ipfsAddress, orcID, githubUserName, eBlocBroker=None, web3=None): #{
    if eBlocBroker == None and web3 == None: #{
        sys.path.insert(1, os.path.join(sys.path[0], '..'))
        from imports import connectEblocBroker
        from imports import getWeb3
        web3           = getWeb3()
        eBlocBroker    = connectEblocBroker(web3)
    #}
    account = web3.eth.accounts[int(accountID)]  # User's Ethereum Address
    
    if isUserExist(account, eBlocBroker, web3):
        return 'User (' + account  + ') is already registered.'
        
    if len(federationCloudID) < 128 and len(userEmail) < 128 and len(orcID) == 19 and orcID.replace("-", "").isdigit(): 
        tx = eBlocBroker.transact({"from":account, "gas": 4500000}).registerUser(userEmail, federationCloudID, miniLockID, ipfsAddress, orcID, githubUserName) 
        return  'Tx: ' + tx.hex()
#}
    
if __name__ == '__main__': #{
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
        userEmail          = "alper.alimoglu@gmail.com" 
        federationCloudID  = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579" 
        miniLockID         = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ" 
        ipfsAddress        = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf" 
        orcID              = "0000-0001-7642-0552" 
        githubUserName     = "eBloc"

    res = registerUser(account, userEmail, federationCloudID, miniLockID, ipfsAddress, orcID, githubUserName)
    print(res)
#}
