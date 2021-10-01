#!/usr/bin/env python3

import sys
import broker.cfg as cfg
from broker._utils.tools import log
from broker.utils import print_tb

if __name__ == "__main__":
    Ebb = cfg.Ebb
    try:
        providers = Ebb.get_providers()
        if len(providers) == 0:
            log("E: There is no registered provider.")

        for provider in providers:
            print(provider)
    except Exception as e:
        print_tb(e)
        sys.exit(1)
