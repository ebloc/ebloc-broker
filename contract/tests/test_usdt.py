#!/usr/bin/python3

from brownie import accounts
from broker.eblocbroker_scripts.utils import Cent


def test_transfer(_Ebb):
    token = _Ebb
    c = Cent("1 usd")  # dummy object
    total_supply = Cent("1000000000 usd")
    assert token.totalSupply() == c.usdt("1000000000") == total_supply

    token.transfer(accounts[1], c.usdt("100"), {"from": accounts[0]})
    assert token.balanceOf(accounts[1]) == c.usdt("100") == Cent("100 usd")
    assert token.balanceOf(accounts[0]) == c.usdt("999999900") == (total_supply.__sub__("100 usd"))

    token.transfer(accounts[1], Cent("10 usd"), {"from": accounts[0]})
    assert token.balanceOf(accounts[1]) == Cent("110 usd")
    assert token.balanceOf(accounts[0]) == total_supply.__sub__("110 usd")
