#!/usr/bin/python3

import pytest
from brownie import accounts

def test_ownership(eB):
    '''Get Owner'''
    assert eB.getOwner() == accounts[0]
    
    with pytest.reverts(): # transferOwnership should revert
        eB.transferOwnership('0x0000000000000000000000000000000000000000', {"from": accounts[0]})

    eB.transferOwnership(accounts[1], {"from": accounts[0]})
    assert eB.getOwner() == accounts[1]   
