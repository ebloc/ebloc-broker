#!/usr/bin/python3

import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # def isolate(module_isolation):
    pass


@pytest.fixture(scope="module")
def eB(Lib, eBlocBroker, accounts):
    accounts[0].deploy(Lib)
    t = accounts[0].deploy(eBlocBroker)
    yield t
