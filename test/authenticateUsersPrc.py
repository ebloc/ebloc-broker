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
from authenticateORCID import authenticateORCID

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)
# -------------------------------------------------------
orcID = '0000-0001-7642-0552'

accounts= ["0x90Eb5E1ADEe3816c85902FA50a240341Fa7d90f5", "0x289C3D804a3B5bEB9C5A542AD2711541cbb1572c", "0xb1FAf341B5c05AfAD8C019d7118f3B2a635b88ED", "0x7A4718561D4B6c06214093Bd22EA074b0C398F5F", "0xaDD445Ce732c425998e3A0c4009fA5DD5E81c995", "0x8A22243ED31966B2DF91CcDd99d1181Fdf6fe546", "0x75e96A39Dd6267A054EC8E0C9942306531d00EA8", "0x6F53FBB4F882C1969271Ad20E2eB68Df0642Dd79", "0x948f9E469a18B72cf960AE51B320503B3b6A603e", "0x496acA2bE0694A1137B05cE7fFDcd982bFb53FAD"];

for i in range(0, len(accounts)):
    print(authenticateORCID(accounts[i], orcID))

'''
userEmail         = "aalimog1@binghamton.edu"
federationCloudID = "3d8e2dc2-b855-1036-807f-9dbd8c6b1579"
miniLockID        = "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k"
orcid             = "0000-0001-7642-0552"
ipfsAddress       = "/ip4/193.140.197.95/tcp/3002/ipfs/QmSdnexZEQGKuj31PqrRP7XNZ4wvKMZWasvhqDYc9Y5G3C"
githubUserName    = "eBloc"

for i in range(0, 10):
    accountID = str(i)
    tx = registerUser(accountID, userEmail, federationCloudID, miniLockID, ipfsAddress, orcid, githubUserName, eBlocBroker, web3)
    print(str(i) + ' | ' + tx)
'''
