#!/usr/bin/python3

"""
For experiment purposes reqisters 10 users from prc-95
"""

from os.path import expanduser

from imports import connect

home = expanduser("~")
eBlocBroker, w3 = connect()

email = "aalimog1@binghamton.edu"
federationCloudID = "059ab6ba-4030-48bb-b81b-12115f531296"
ipfsAddress = "/ip4/193.140.197.95/tcp/3002/ipfs/QmSdnexZEQGKuj31PqrRP7XNZ4wvKMZWasvhqDYc9Y5G3C"
githubUsername = "eBloc"

accoutLength = 10
for i in range(0, accoutLength):
    account_id = str(i)
    account = w3.eth.accounts[i]
    tx = register_requester(account_id, email, federationCloudID, ipfsAddress, githubUsername)
    print(account + " | " + str(i) + " | " + tx)

print("")
print("[", end="")
for i in range(0, accoutLength):
    print('"' + w3.eth.accounts[i] + '"', end="")
    if i != accoutLength - 1:
        print(", ", end="")
print("]")
