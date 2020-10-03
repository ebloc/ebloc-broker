#!/usr/bin/env python3

import daemon

import libs.ipfs as ipfs
from config import env
from utils import is_ipfs_on, popen_communicate


def run():
    # https://stackoverflow.com/a/8375012/2402577
    print("running ipfs")
    with daemon.DaemonContext():
        cmd = ["ipfs", "daemon"]  # , "--mount"]
        popen_communicate(cmd, env.IPFS_LOG)

    # ipfs mounted at: /ipfs
    # success, output = run_command(["sudo", "ipfs", "mount", "-f", "/ipfs"])
    # logging.info(output)


if __name__ == "__main__":
    if not is_ipfs_on():
        ipfs.remove_lock_files()
        run()
