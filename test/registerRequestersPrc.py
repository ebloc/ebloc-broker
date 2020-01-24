#!/usr/bin/python3

"""
For experiment purposes reqisters 10 users from prc-95
"""

from os.path import expanduser
from imports import connectEblocBroker
from imports import getWeb3
from contractCalls.register_requester import register_requester

home = expanduser("~")
web3 = getWeb3()
eBlocBroker = connectEblocBroker(web3)

email = "aalimog1@binghamton.edu"
federationCloudID = "059ab6ba-4030-48bb-b81b-12115f531296"
miniLockID = "jj2Fn8St9tzLeErBiXA6oiZatnDwJ2YrnLY3Uyn4msD8k"
ipfsAddress = "/ip4/193.140.197.95/tcp/3002/ipfs/QmSdnexZEQGKuj31PqrRP7XNZ4wvKMZWasvhqDYc9Y5G3C"
githubUsername = "eBloc"

accoutLength = 10
for i in range(0, accoutLength):
    accountID = str(i)
    account = web3.eth.accounts[i]
    tx = register_requester(
        accountID, email, federationCloudID, miniLockID, ipfsAddress, githubUsername, eBlocBroker, web3
    )
    print(account + " | " + str(i) + " | " + tx)
print("")
print("[", end="")
for i in range(0, accoutLength):
    print('"' + web3.eth.accounts[i] + '"', end="")
    if i != accoutLength - 1:
        print(", ", end="")
print("]")
