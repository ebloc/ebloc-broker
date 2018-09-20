#!/usr/bin/python

'''
For experiment purposes reqisters 10 users at prc-95
'''

import os, sys
from os.path import expanduser
home = expanduser("~")

sys.path.append(home + "/eBlocBroker")
from imports import connectEblocBroker
from imports import getWeb3

sys.path.insert(0, './contractCalls') 
from contractCalls.registerUser   import registerUser

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)

# -------------------------------------------------------

userEmail         = "aalimog1@binghamton.edu";
federationCloudID = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579";
miniLockID        = "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k";
orcid             = "0000-0001-7642-0552";
ipfsAddress       = "/ip4/193.140.197.95/tcp/3002/ipfs/QmSdnexZEQGKuj31PqrRP7XNZ4wvKMZWasvhqDYc9Y5G3C";
githubUserName    = "eBloc";

for x in range(0, 10): #{
    accountID = str(x);
    tx = registerUser(accountID, userEmail, federationCloudID, miniLockID, ipfsAddress, orcid, githubUserName, eBlocBroker, web3)
    print(str(x) + ' ' + tx);
#}
