#!/usr/bin/env python3

from broker._utils.tools import timenow

if __name__ == "__main__":
    import broker.eblocbroker.Contract as Contract

    Ebb: "Contract.Contract" = Contract.EBB()
    _timenow = Ebb.timenow()
    t = timenow()
    print(f"==> bloxberg_time={_timenow}")
    print(f"==> machine_time={t}")
    print(f"difference_in_seconds={t - _timenow}")
