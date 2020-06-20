#!/usr/bin/env python3

import sys

import daemon

from config import env
from utils import is_ganache_on, popen_communicate


def run(port):
    # https://stackoverflow.com/a/8375012/2402577
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
        port = str(sys.argv[1])
    else:
        port = 8545

    if not is_ganache_on(port):
        print("Running Ganache CLI")
        run(port)
