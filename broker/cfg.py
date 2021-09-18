#!/usr/bin/env python3

"""Global variables for all files.

__ https://stackoverflow.com/a/12413139/2402577
"""


class _Ipfs:
    def __init__(self):
        self.ipfs = None

    def __getattr__(self, name):
        """Return Ipfs object."""
        if not self.ipfs:
            from broker.libs.ipfs import Ipfs

            self.ipfs = Ipfs()

        return getattr(self.ipfs, name)


class W3:
    def __init__(self):
        self.w3 = None

    def __getattr__(self, name):
        """Return web3 object."""
        if not self.w3:
            from brownie import web3

            self.w3: "web3" = web3

        return getattr(self.w3, name)


ipfs = _Ipfs()
w3 = W3()
