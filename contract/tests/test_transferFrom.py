#!/usr/bin/python3

"""
Token implementation Testing.

Link:
__ https://github.com/brownie-mix/token-mix/blob/master/tests/test_transferFrom.py
__ https://eth-brownie.readthedocs.io/en/stable/init.html#init
"""

import brownie
import contract.tests.cfg as _cfg


def test_sender_balance_decreases(accounts, _Ebb):
    sender_balance = _cfg.TOKEN.balanceOf(accounts[0])
    amount = sender_balance // 4

    _cfg.TOKEN.approve(accounts[1], amount, {"from": accounts[0]})
    _cfg.TOKEN.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert _cfg.TOKEN.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, _Ebb):
    receiver_balance = _cfg.TOKEN.balanceOf(accounts[2])
    amount = _cfg.TOKEN.balanceOf(accounts[0]) // 4

    _cfg.TOKEN.approve(accounts[1], amount, {"from": accounts[0]})
    _cfg.TOKEN.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert _cfg.TOKEN.balanceOf(accounts[2]) == receiver_balance + amount


def test_caller_balance_not_affected(accounts, _Ebb):
    caller_balance = _cfg.TOKEN.balanceOf(accounts[1])
    amount = _cfg.TOKEN.balanceOf(accounts[0])

    _cfg.TOKEN.approve(accounts[1], amount, {"from": accounts[0]})
    _cfg.TOKEN.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert _cfg.TOKEN.balanceOf(accounts[1]) == caller_balance


def test_caller_approval_affected(accounts, _Ebb):
    approval_amount = _cfg.TOKEN.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    _cfg.TOKEN.approve(accounts[1], approval_amount, {"from": accounts[0]})
    _cfg.TOKEN.transferFrom(accounts[0], accounts[2], transfer_amount, {"from": accounts[1]})

    assert _cfg.TOKEN.allowance(accounts[0], accounts[1]) == approval_amount - transfer_amount


def test_receiver_approval_not_affected(accounts, _Ebb):
    approval_amount = _cfg.TOKEN.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    _cfg.TOKEN.approve(accounts[1], approval_amount, {"from": accounts[0]})
    _cfg.TOKEN.approve(accounts[2], approval_amount, {"from": accounts[0]})
    _cfg.TOKEN.transferFrom(accounts[0], accounts[2], transfer_amount, {"from": accounts[1]})

    assert _cfg.TOKEN.allowance(accounts[0], accounts[2]) == approval_amount


def test_total_supply_not_affected(accounts, _Ebb):
    total_supply = _cfg.TOKEN.totalSupply()
    amount = _cfg.TOKEN.balanceOf(accounts[0])

    _cfg.TOKEN.approve(accounts[1], amount, {"from": accounts[0]})
    _cfg.TOKEN.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert _cfg.TOKEN.totalSupply() == total_supply


def test_returns_true(accounts, _Ebb):
    amount = _cfg.TOKEN.balanceOf(accounts[0])
    _cfg.TOKEN.approve(accounts[1], amount, {"from": accounts[0]})
    tx = _cfg.TOKEN.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, _Ebb):
    amount = _cfg.TOKEN.balanceOf(accounts[0])
    receiver_balance = _cfg.TOKEN.balanceOf(accounts[2])

    _cfg.TOKEN.approve(accounts[1], amount, {"from": accounts[0]})
    _cfg.TOKEN.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert _cfg.TOKEN.balanceOf(accounts[0]) == 0
    assert _cfg.TOKEN.balanceOf(accounts[2]) == receiver_balance + amount


def test_transfer_zero__Ebbs(accounts, _Ebb):
    sender_balance = _cfg.TOKEN.balanceOf(accounts[0])
    receiver_balance = _cfg.TOKEN.balanceOf(accounts[2])

    _cfg.TOKEN.approve(accounts[1], sender_balance, {"from": accounts[0]})
    _cfg.TOKEN.transferFrom(accounts[0], accounts[2], 0, {"from": accounts[1]})

    assert _cfg.TOKEN.balanceOf(accounts[0]) == sender_balance
    assert _cfg.TOKEN.balanceOf(accounts[2]) == receiver_balance


def test_transfer_zero__Ebbs_without_approval(accounts, _Ebb):
    sender_balance = _cfg.TOKEN.balanceOf(accounts[0])
    receiver_balance = _cfg.TOKEN.balanceOf(accounts[2])

    _cfg.TOKEN.transferFrom(accounts[0], accounts[2], 0, {"from": accounts[1]})

    assert _cfg.TOKEN.balanceOf(accounts[0]) == sender_balance
    assert _cfg.TOKEN.balanceOf(accounts[2]) == receiver_balance


def test_insufficient_balance(accounts, _Ebb):
    balance = _cfg.TOKEN.balanceOf(accounts[0])

    _cfg.TOKEN.approve(accounts[1], balance + 1, {"from": accounts[0]})
    with brownie.reverts():
        _cfg.TOKEN.transferFrom(accounts[0], accounts[2], balance + 1, {"from": accounts[1]})


def test_insufficient_approval(accounts, _Ebb):
    balance = _cfg.TOKEN.balanceOf(accounts[0])

    _cfg.TOKEN.approve(accounts[1], balance - 1, {"from": accounts[0]})
    with brownie.reverts():
        _cfg.TOKEN.transferFrom(accounts[0], accounts[2], balance, {"from": accounts[1]})


def test_no_approval(accounts, _Ebb):
    balance = _cfg.TOKEN.balanceOf(accounts[0])

    with brownie.reverts():
        _cfg.TOKEN.transferFrom(accounts[0], accounts[2], balance, {"from": accounts[1]})


def test_revoked_approval(accounts, _Ebb):
    balance = _cfg.TOKEN.balanceOf(accounts[0])

    _cfg.TOKEN.approve(accounts[1], balance, {"from": accounts[0]})
    _cfg.TOKEN.approve(accounts[1], 0, {"from": accounts[0]})

    with brownie.reverts():
        _cfg.TOKEN.transferFrom(accounts[0], accounts[2], balance, {"from": accounts[1]})


def test_transfer_to_self(accounts, _Ebb):
    sender_balance = _cfg.TOKEN.balanceOf(accounts[0])
    amount = sender_balance // 4

    _cfg.TOKEN.approve(accounts[0], sender_balance, {"from": accounts[0]})
    _cfg.TOKEN.transferFrom(accounts[0], accounts[0], amount, {"from": accounts[0]})

    assert _cfg.TOKEN.balanceOf(accounts[0]) == sender_balance
    assert _cfg.TOKEN.allowance(accounts[0], accounts[0]) == sender_balance - amount


def test_transfer_to_self_no_approval(accounts, _Ebb):
    amount = _cfg.TOKEN.balanceOf(accounts[0])

    with brownie.reverts():
        _cfg.TOKEN.transferFrom(accounts[0], accounts[0], amount, {"from": accounts[0]})


def test_transfer_event_fires(accounts, _Ebb):
    amount = _cfg.TOKEN.balanceOf(accounts[0])

    _cfg.TOKEN.approve(accounts[1], amount, {"from": accounts[0]})
    tx = _cfg.TOKEN.transferFrom(accounts[0], accounts[2], amount, {"from": accounts[1]})

    assert len(tx.events) == 2
    assert tx.events["Transfer"].values() == [accounts[0], accounts[2], amount]
