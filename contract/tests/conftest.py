#!/usr/bin/python3

import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # def isolate(module_isolation):
    pass


@pytest.fixture(scope="module")
def _Ebb(Lib, eBlocBroker, accounts):
    accounts[0].deploy(Lib)
    yield accounts[0].deploy(eBlocBroker)
