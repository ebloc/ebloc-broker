#!/usr/bin/python3

import pytest

import contract.tests.cfg as _cfg


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # def isolate(module_isolation):
    pass


@pytest.fixture(scope="module")
def _Ebb(USDTmy, Lib, eBlocBroker, accounts):
    _cfg.TOKEN = tx = USDTmy.deploy({"from": accounts[0]})
    print(tx.address)
    accounts[0].deploy(Lib)
    yield eBlocBroker.deploy(tx.address, {"from": accounts[0]})
