import pytest
from tests import test_eblocbroker

import contract.scripts.lib
from brownie import *
from utils import ZERO_ADDRESS


def project():
    print("ben_is_awesome_and_king")
    accounts[0].deploy(Lib)
    Ebb = accounts[0].deploy(eBlocBroker)

    print(Ebb.getOwner())

    try:
        tx = Ebb.transferOwnership(ZERO_ADDRESS, {"from": accounts[0]}).raisingFunction()
    except:
        tx = history[-1]
        print(tx.revert_msg)

    print("END")
