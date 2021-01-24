#!/usr/bin/env python3

import sys
import time

import daemon

from broker.config import env
from broker.utils import is_ganache_on, is_npm_installed, log, popen_communicate


def run(port, hardfork_name):
    """Run daemon.

    https://stackoverflow.com/a/8375012/2402577
    """
    print("Running Ganache CLI")
    with daemon.DaemonContext():
        cmd = [
            "ganache-cli",
            "--port",
            port,
            "--gasLimit",
            "6721975",
            "--accounts",
            "10",
            "--hardfork",
            "istanbul",
            "--allowUnlimitedContractSize",
        ]
        popen_communicate(cmd, env.GANACHE_LOG)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        port = 8545  # default port number

    hardfork_name = "istanbul"
    npm_package = "ganache-cli"
    if not is_npm_installed(npm_package):
        log(f"E: {npm_package} is not installed within npm", color="red")
        sys.exit()

    if not is_ganache_on(port):
        run(port, hardfork_name)
        time.sleep(0.25)
