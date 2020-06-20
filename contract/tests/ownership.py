#!/usr/bin/python3

import pytest

from brownie import accounts
from utils import ZERO_ADDRESS


def test_ownership(Ebb):
    """Get Owner"""
    assert Ebb.getOwner() == accounts[0]

    with pytest.reverts():  # transferOwnership should revert
        Ebb.transferOwnership(ZERO_ADDRESS, {"from": accounts[0]})

    Ebb.transferOwnership(accounts[1], {"from": accounts[0]})
    assert Ebb.getOwner() == accounts[1]
