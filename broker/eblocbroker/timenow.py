#!/usr/bin/env python3

from broker import cfg
from broker._utils.tools import timenow

if __name__ == "__main__":
    Ebb = cfg.Ebb
    _timenow = Ebb.timenow()
    system_time = timenow()
    print(f"==> bloxberg_time={_timenow}")
    print(f"==> machine_time={system_time}")
    print(f"difference_in_seconds={system_time - _timenow}")
