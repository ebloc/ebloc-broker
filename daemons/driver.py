#!/usr/bin/env python3

import daemon

from config import env
from utils import is_driver_on, popen_communicate


def run():
    with daemon.DaemonContext():
        cmd = ["python3", "Driver"]
        popen_communicate(cmd, env.DRIVER_LOG)


if __name__ == "__main__":
    if not is_driver_on():
        run()
