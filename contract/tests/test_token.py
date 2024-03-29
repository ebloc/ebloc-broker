#!/usr/bin/python3

import brownie
import contract.tests.cfg as _cfg


def test_sender_balance_decreases(accounts, _Ebb):
    sender_balance = _cfg.TOKEN.balanceOf(accounts[0])
    amount = sender_balance // 4
    _cfg.TOKEN.transfer(accounts[1], amount, {"from": accounts[0]})
    assert _cfg.TOKEN.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, _Ebb):
    receiver_balance = _cfg.TOKEN.balanceOf(accounts[1])
    amount = _cfg.TOKEN.balanceOf(accounts[0]) // 4

    _cfg.TOKEN.transfer(accounts[1], amount, {"from": accounts[0]})

    assert _cfg.TOKEN.balanceOf(accounts[1]) == receiver_balance + amount


def test_total_supply_not_affected(accounts, _Ebb):
    total_supply = _cfg.TOKEN.totalSupply()
    amount = _cfg.TOKEN.balanceOf(accounts[0])

    _cfg.TOKEN.transfer(accounts[1], amount, {"from": accounts[0]})

    assert _cfg.TOKEN.totalSupply() == total_supply


def test_returns_true(accounts, _Ebb):
    amount = _cfg.TOKEN.balanceOf(accounts[0])
    tx = _cfg.TOKEN.transfer(accounts[1], amount, {"from": accounts[0]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, _Ebb):
    amount = _cfg.TOKEN.balanceOf(accounts[0])
    receiver_balance = _cfg.TOKEN.balanceOf(accounts[1])

    _cfg.TOKEN.transfer(accounts[1], amount, {"from": accounts[0]})

    assert _cfg.TOKEN.balanceOf(accounts[0]) == 0
    assert _cfg.TOKEN.balanceOf(accounts[1]) == receiver_balance + amount


def test_transfer_zero__Ebbs(accounts, _Ebb):
    sender_balance = _cfg.TOKEN.balanceOf(accounts[0])
    receiver_balance = _cfg.TOKEN.balanceOf(accounts[1])

    _cfg.TOKEN.transfer(accounts[1], 0, {"from": accounts[0]})

    assert _cfg.TOKEN.balanceOf(accounts[0]) == sender_balance
    assert _cfg.TOKEN.balanceOf(accounts[1]) == receiver_balance


def test_transfer_to_self(accounts, _Ebb):
    sender_balance = _cfg.TOKEN.balanceOf(accounts[0])
    amount = sender_balance // 4

    _cfg.TOKEN.transfer(accounts[0], amount, {"from": accounts[0]})

    assert _cfg.TOKEN.balanceOf(accounts[0]) == sender_balance


def test_insufficient_balance(accounts, _Ebb):
    balance = _cfg.TOKEN.balanceOf(accounts[0])

    with brownie.reverts():
        _cfg.TOKEN.transfer(accounts[1], balance + 1, {"from": accounts[0]})


def test_transfer_event_fires(accounts, _Ebb):
    amount = _cfg.TOKEN.balanceOf(accounts[0])
    tx = _cfg.TOKEN.transfer(accounts[1], amount, {"from": accounts[0]})

    assert len(tx.events) == 1
    assert tx.events["Transfer"].values() == [accounts[0], accounts[1], amount]
