#!/usr/bin/python3

"""
Token implementation testing.

Link:
__ https://github.com/brownie-mix/token-mix/blob/master/tests/test_approve.py
__ https://eth-brownie.readthedocs.io/en/stable/init.html#init
"""

import pytest


@pytest.mark.parametrize("idx", range(5))
def test_initial_approval_is_zero(_Ebb, accounts, idx):
    assert _Ebb.allowance(accounts[0], accounts[idx]) == 0


def test_approve(_Ebb, accounts):
    _Ebb.approve(accounts[1], 10**2, {"from": accounts[0]})

    assert _Ebb.allowance(accounts[0], accounts[1]) == 10**2


def test_modify_approve(_Ebb, accounts):
    _Ebb.approve(accounts[1], 10**2, {"from": accounts[0]})
    _Ebb.approve(accounts[1], 12345678, {"from": accounts[0]})

    assert _Ebb.allowance(accounts[0], accounts[1]) == 12345678


def test_revoke_approve(_Ebb, accounts):
    _Ebb.approve(accounts[1], 10**2, {"from": accounts[0]})
    _Ebb.approve(accounts[1], 0, {"from": accounts[0]})

    assert _Ebb.allowance(accounts[0], accounts[1]) == 0


def test_approve_self(_Ebb, accounts):
    _Ebb.approve(accounts[0], 10**2, {"from": accounts[0]})

    assert _Ebb.allowance(accounts[0], accounts[0]) == 10**2


def test_only_affects_target(_Ebb, accounts):
    _Ebb.approve(accounts[1], 10**2, {"from": accounts[0]})

    assert _Ebb.allowance(accounts[1], accounts[0]) == 0


def test_returns_true(_Ebb, accounts):
    tx = _Ebb.approve(accounts[1], 10**2, {"from": accounts[0]})

    assert tx.return_value is True


def test_approval_event_fires(accounts, _Ebb):
    tx = _Ebb.approve(accounts[1], 10**2, {"from": accounts[0]})

    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [accounts[0], accounts[1], 10**2]
