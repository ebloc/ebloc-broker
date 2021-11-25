#!/usr/bin/env python3

from broker import cfg
from broker._utils._log import log
from broker._utils.tools import timenow


def print_timenow():
    Ebb = cfg.Ebb
    _timenow = Ebb.timenow()
    system_time = timenow()
    log(f"==> bloxberg_time={_timenow}")
    log(f"==> machine_time={system_time}")
    log(f"\tdifference_in_seconds={system_time - _timenow}", "bold")


if __name__ == "__main__":
    print_timenow()
