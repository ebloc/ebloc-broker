#!/usr/bin/env python3

import sys

import daemon
import daemon.pidfile
from daemons.daemon_base import Daemon_base

from broker._utils.tools import QuietExit
from broker.config import env
from broker.utils import is_driver_on, print_tb


def main():
    pidfile = daemon.pidfile.PIDLockFile(env.DRIVER_DAEMON_LOCK)
    cmd = ["python3", "Driver.py"]
    daemon_base = Daemon_base(pidfile, env.EBLOCPATH, cmd)
    if len(sys.argv) == 2:
        if sys.argv[1] in ["start", "s"]:
            try:
                is_driver_on()
                daemon_base.start()
            except QuietExit:
                pass
            except Exception as e:
                print_tb(e)
                sys.exit(1)
        elif sys.argv[1] in ["terminate", "t"]:
            daemon_base.terminate()
        elif sys.argv[1] in ["reload", "r"]:
            daemon_base.restart()
        else:
            print("Unknown command")
            sys.exit(2)
            sys.exit(0)
    else:
        print("usage: %s [s]tart|[t]erminate|[r]eload" % sys.argv[0])
        sys.exit(2)

if __name__ == "__main__":
    main()
