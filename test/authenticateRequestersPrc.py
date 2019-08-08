#!/usr/bin/python3

'''
For experiment purposes reqisters 10 users from prc-95
'''

import os, sys
from os.path import expanduser
home = expanduser("~")
from imports import connectEblocBroker, getWeb3
from contractCalls.authenticateORCID import authenticateORCID

web3        = getWeb3()
eBlocBroker = connectEblocBroker(web3)
# -------------------------------------------------------
orcID = '0000-0001-7642-0552'

# Registered addresses on PRC-95
accounts=["0x90Eb5E1ADEe3816c85902FA50a240341Fa7d90f5", "0x289C3D804a3B5bEB9C5A542AD2711541cbb1572c", "0xb1FAf341B5c05AfAD8C019d7118f3B2a635b88ED", "0x7A4718561D4B6c06214093Bd22EA074b0C398F5F", "0xaDD445Ce732c425998e3A0c4009fA5DD5E81c995", "0x8A22243ED31966B2DF91CcDd99d1181Fdf6fe546", "0x75e96A39Dd6267A054EC8E0C9942306531d00EA8", "0x6F53FBB4F882C1969271Ad20E2eB68Df0642Dd79", "0x948f9E469a18B72cf960AE51B320503B3b6A603e", "0x496acA2bE0694A1137B05cE7fFDcd982bFb53FAD"]

for i in range(0, len(accounts)):
    print(authenticateORCID(accounts[i], orcID))
