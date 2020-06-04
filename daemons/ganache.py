#!/usr/bin/env python3

import daemon

from config import env
from utils import is_ganache_on, popen_communicate


def run():
    # https://stackoverflow.com/a/8375012/2402577
    with daemon.DaemonContext():
        cmd = [
            "ganache-cli",
            "--port",
            "8546",
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
    if not is_ganache_on():
        print("Running Ganache CLI")
        run()
