#!/usr/bin/python3

import brownie
import pytest
import random

roc = None
zero = "0x00000000000000000000000000000000"


@pytest.fixture(scope="module", autouse=True)
def my_own_session_run_at_beginning(_Roc):
    global roc  # type: ignore
    roc = _Roc


def md5_hash():
    _hash = random.getrandbits(128)
    return "%032x" % _hash


def test_roc(web3, accounts):
    assert roc.getDataHashLen() == 0
    _hash = md5_hash()
    roc.createCertificate(accounts[0], _hash, {"from": accounts[0]})
    assert roc.getDataHashLen() == 1
    assert str(roc.getDataHash(0)).replace(zero, "") == _hash
    assert str(roc.tokenHash(1)).replace(zero, "") == _hash
    assert roc.getTokenIndex(_hash) == 1
    assert roc.ownerOf(1) == accounts[0]
    with brownie.reverts():
        roc.createCertificate(accounts[0], _hash, {"from": accounts[0]})
