#!/usr/bin/env python3

import os
import sys

from imports import connect

eBlocBroker, w3 = connect()
if eBlocBroker is None or w3 is None:
    sys.exit(1)

os.chdir(sys.path[0])

# eBloc-NAS
account = w3.eth.accounts[0]  # Provider's Ethereum Address
coreNumber = 2
providerEmail = "alper.alimoglu@gmail.com"
federationCloudId = "ee14ea28-b869-1036-8080-9dbd8c6b1579@b2drop.eudat.eu"
minilock_id = "9VZyJy1gRFJfdDtAjRitqmjSxPjSAjBR6BxH59UeNgKzQ"
corePriceMinuteWei = 100
ipfsAddress = "/ip4/79.123.177.145/tcp/4001/ipfs/QmWmZQnb8xh3gHf9ZFmVQC4mLEav3Uht5kHJxZtixG3rsf"


# TETAM
account = w3.eth.accounts[0]  # Provider's Ethereum Address
coreNumber = 128
providerEmail = "alper01234alper@gmail.com"
federationCloudId = ""
minilock_id = ""
corePriceMinuteWei = 100
ipfsAddress = "/ip4/193.140.196.159/tcp/4001/ipfs/QmNQ74xaWquZseMhZJCPfV47WttP9hAoPEXeCMKsh3Cap4"


# Google-Drive Instance-1
account = w3.eth.accounts[0]  # Provider's Ethereum Address
coreNumber = 64
providerEmail = ""
federationCloudId = "SjPmN3Fet4bKSBJAutnAwA15ct9UciNBNYo1BQCFiEjHn"
minilock_id = ""
corePriceMinuteWei = 100
ipfsAddress = "/ip4/34.73.108.63/tcp/4001/ipfs/QmXqUW6n57c2e4Y6461CiNkdSuYEGtnNYrWHCVeNEcW3Td"

# Google-Drive Instance-2
account = w3.eth.accounts[0]  # Provider's Ethereum Address
coreNumber = 64
providerEmail = ""
federationCloudId = ""
minilock_id = ""
corePriceMinuteWei = 100
ipfsAddress = "/ip4/35.243.200.173/tcp/4001/ipfs/QmYCXLnAw7XAQjbKacZZQer7wdBd8YpAMVxvA4U1KCmWC2"
