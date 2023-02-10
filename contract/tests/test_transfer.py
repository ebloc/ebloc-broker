#!/usr/bin/python3

from brownie import accounts
from broker.eblocbroker_scripts.utils import Cent


def decimals():
    return 2


def usdt(bal):
    return float(bal) * (10 ** decimals())


def test_transfer(_Ebb):
    token = _Ebb
    total_supply = Cent("1000000000 usd")
    assert token.totalSupply() == usdt("1000000000") == total_supply

    token.transfer(accounts[1], usdt("100"), {"from": accounts[0]})
    assert token.balanceOf(accounts[1]) == usdt("100") == Cent("100 usd")
    assert token.balanceOf(accounts[0]) == usdt("999999900") == (total_supply.__sub__("100 usd"))

    token.transfer(accounts[1], Cent("10 usd"), {"from": accounts[0]})
    assert token.balanceOf(accounts[1]) == Cent("110 usd")
    assert token.balanceOf(accounts[0]) == total_supply.__sub__("110 usd")
