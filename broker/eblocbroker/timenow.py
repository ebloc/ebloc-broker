#!/usr/bin/env python3

from datetime import datetime

from broker._utils.tools import _time, _timestamp, timenow

if __name__ == "__main__":
    import broker.eblocbroker.Contract as Contract

    Contract.eblocbroker = Contract.Contract()
    _timenow = Contract.eblocbroker.timenow()
    t = timenow()
    print(_timenow)
    print(t)
    print(t - _timenow)
