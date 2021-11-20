#!/usr/bin/env python3

import sys
import time

import daemon

from broker.config import env
from broker.utils import is_ganache_on, is_npm_installed, log, popen_communicate


def run(port=8545, hardfork_name="istanbul"):
    """Run ganache daemon on the background.

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
            {hardfork_name},
            "--allowUnlimitedContractSize",
        ]
        popen_communicate(cmd, env.GANACHE_LOG)


if __name__ == "__main__":
    port = 8545
    if len(sys.argv) == 2:
        port = int(sys.argv[1])

    npm_package = "ganache-cli"
    if not is_npm_installed(npm_package):
        log(f"E: {npm_package} is not installed within npm")
        sys.exit()

    if not is_ganache_on(port):
        run(port)
        time.sleep(0.25)
