#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils.tools import log
from broker.errors import QuietExit
from broker.utils import print_tb

if __name__ == "__main__":
    Ebb = cfg.Ebb
    try:
        providers = Ebb.get_providers()
        if len(providers) == 0:
            log("E: There is no registered provider")
        else:
            log("providers:", "bold green")

        for provider in providers:
            log(provider.lower())
    except QuietExit:
        sys.exit(1)
    except Exception as e:
        print_tb(e)
        sys.exit(1)
