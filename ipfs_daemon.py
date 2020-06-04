#!/usr/bin/env python3

import daemon

from config import env
from lib import is_ipfs_on, silent_remove
from utils import popen_communicate


def run():
    silent_remove(f"{env.HOME}/.ipfs/datastore/LOCK")
    silent_remove(f"{env.HOME}/.ipfs/repo.lock")

    # https://stackoverflow.com/a/8375012/2402577
    with daemon.DaemonContext():
        cmd = ["ipfs", "daemon"]  # , "--mount"]
        popen_communicate(cmd, env.IPFS_LOG)

    # ipfs mounted at: /ipfs
    # success, output = run_command(["sudo", "ipfs", "mount", "-f", "/ipfs"])
    # logging.info(output)


if __name__ == "__main__":
    if not is_ipfs_on():
        run()
