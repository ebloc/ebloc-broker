#!/usr/bin/python3

import pytest

from brownie import accounts

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def test_ownership(Ebb):
    """Test ownership of the contract."""
    assert Ebb.getOwner() == accounts[0]
    with pytest.reverts():
        Ebb.transferOwnership(ZERO_ADDRESS, {"from": accounts[0]})

    Ebb.transferOwnership(accounts[1], {"from": accounts[0]})
    assert Ebb.getOwner() == accounts[1]
