#!/usr/bin/env python3

from broker import cfg
from broker._utils.tools import log
from broker.errors import QuietExit
from broker.utils import print_tb


def main():
    providers = Ebb.get_providers()
    if len(providers) == 0:
        log("E: [green]There is no registered provider")
    else:
        log("providers:", "green")

    for provider in providers:
        log(f"\t{provider.lower()}", "cyan", h=False)


if __name__ == "__main__":
    Ebb = cfg.Ebb
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"==> {e}")
    except Exception as e:
        print_tb(str(e))
