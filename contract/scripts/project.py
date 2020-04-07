import pytest
from brownie import *
from tests import test_eblocbroker

import scripts.lib


def project():
    print("ben_is_awesome_and_king")
    accounts[0].deploy(Lib)
    eB = accounts[0].deploy(eBlocBroker)

    print(eB.getOwner())

    try:
        tx = eB.transferOwnership("0x0000000000000000000000000000000000000000", {"from": accounts[0]}).raisingFunction()
    except:
        tx = history[-1]
        print(tx.revert_msg)

    print("END")
