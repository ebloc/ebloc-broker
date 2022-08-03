#!/usr/bin/env python3

import sys

from daemons.prefab import run

from broker._utils import tools
from broker.config import env
from broker.errors import QuietExit
from broker.utils import is_driver_on, print_tb


class DriverDaemon(run.RunDaemon):  # pylint: disable=too-many-ancestors
    def run(self):
        tools.run(["eblocbroker", "driver"])


def main():
    pidfile = env.DRIVER_DAEMON_LOCK
    d = DriverDaemon(pidfile=pidfile)
    # pidfile = daemon.pidfile.PIDLockFile(env.DRIVER_DAEMON_LOCK)
    # logfile = os.path.join(os.getcwd(), "sleepy.log")
    # pidfile = os.path.join(os.getcwd(), "sleepy.pid")
    # logging.basicConfig(filename=logfile, level=logging.DEBUG)
    # d = Daemon_base(pidfile, env.EBLOCPATH, cmd)
    if len(sys.argv) == 2:
        if sys.argv[1] in ["start", "s"]:
            try:
                is_driver_on()
                d.start()
            except QuietExit:
                pass
            except Exception as e:
                print_tb(str(e))
                sys.exit(1)
        elif sys.argv[1] in ["terminate", "t"]:
            d.terminate()
        elif sys.argv[1] in ["reload", "r"]:
            d.restart()
        else:
            print("E: unknown command")
            sys.exit(2)
            sys.exit(0)
    else:
        print("usage: %s [s]tart|[t]erminate|[r]eload" % sys.argv[0])
        sys.exit(2)


if __name__ == "__main__":
    main()
