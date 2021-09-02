#!/usr/bin/env python3

"""Global variables for all files."""

from web3 import IPCProvider, Web3  # noqa
from broker.libs.ipfs import Ipfs

ipfs = Ipfs()
w3: Web3 = None
