import pytest
from tests import test_eblocbroker

import contract.scripts.lib
from brownie import *
from utils import ZERO_ADDRESS


def project():
    accounts[0].deploy(Lib)
    ebb = accounts[0].deploy(eBlocBroker)

    print(ebb.getOwner())

    try:
        tx = ebb.transferOwnership(ZERO_ADDRESS, {"from": accounts[0]}).raisingFunction()
    except:
        tx = history[-1]
        print(tx.revert_msg)

    print("END")
