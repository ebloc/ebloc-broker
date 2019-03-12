#!/usr/bin/python3

'''
For experiment purposes reqisters 10 users from prc-95
'''

import os, sys
from os.path import expanduser
home = expanduser("~")

sys.path.append(home + '/eBlocBroker')
from imports import connectEblocBroker
from imports import getWeb3

sys.path.insert(0, home + '/eBlocBroker/contractCalls')
from registerUser import registerUser

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)
# -------------------------------------------------------

userEmail         = "aalimog1@binghamton.edu"
federationCloudID = "059ab6ba-4030-48bb-b81b-12115f531296"
miniLockID        = "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k"
ipfsAddress       = "/ip4/193.140.197.95/tcp/3002/ipfs/QmSdnexZEQGKuj31PqrRP7XNZ4wvKMZWasvhqDYc9Y5G3C"
githubUserName    = "eBloc"

accoutLength = 10
for i in range(0, accoutLength):
    accountID = str(i)
    account = web3.eth.accounts[i]
    tx = registerUser(accountID, userEmail, federationCloudID, miniLockID, ipfsAddress, githubUserName, eBlocBroker, web3)
    print(account + ' | ' + str(i) + ' | ' +  tx)
print('')
print('[', end='')
for i in range(0, accoutLength):
    print("\"" + web3.eth.accounts[i] + "\"", end='')
    if i != accoutLength-1:
        print(', ', end='')
print(']')
