#!/usr/bin/env python3

"""Global variables for all files.

__ https://stackoverflow.com/a/12413139/2402577
"""
from rich.console import Console

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
IS_THREADING_ENABLED = True
IS_BROWNIE_TEST = False
IS_PRIVATE_IPFS = False
IS_BREAKPOINT = False
IS_THREAD_JOIN = False
TX_TIMEOUT = 1800
IS_THREAD_JOIN = False
IS_FULL_TEST = False  # check whether the full-long test is          applied
RECONNECT_ATTEMPTS: int = 5
BLOCK_DURATION: int = 6
ONE_HOUR_BLOCK_DURATION: int = int(3600 / BLOCK_DURATION)
ONE_DAY_BLOCK_DURATION: int = ONE_HOUR_BLOCK_DURATION * 24
IPFS_TIMEOUT: int = 300


class EBB:
    def __init__(self):
        self.eblocbroker = None

    def __getattr__(self, name):
        """Return the 'Contract' object."""
        if not self.eblocbroker:
            from broker.eblocbroker_scripts.Contract import Contract

            global Ebb  # type: ignore
            self.eblocbroker: "Contract" = Contract()
            Ebb = self.eblocbroker

        return getattr(self.eblocbroker, name)


class _Ipfs:
    def __init__(self):
        self.ipfs = None

    def __getattr__(self, name):
        """Return the `Ipfs` object."""
        if not self.ipfs:
            from broker.libs.ipfs import Ipfs

            global ipfs  # type: ignore
            self.ipfs: "Ipfs" = Ipfs()
            ipfs = self.ipfs

        return getattr(self.ipfs, name)


class W3:
    def __init__(self):
        self.w3 = None

    def __getattr__(self, name):
        """Return the `web3` object."""
        if not self.w3:
            from brownie import web3

            global w3  # type: ignore
            self.w3: "web3" = web3
            w3 = self.w3

        return getattr(self.w3, name)


console = Console()
Ebb = EBB()
ipfs = _Ipfs()
w3 = W3()
