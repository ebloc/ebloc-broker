#!/usr/bin/env python3

import sys

import daemon

from broker.config import env
from broker.utils import is_ganache_on, popen_communicate

# from broker import cfg
# from broker.utils import is_npm_installed, log


def run(port=8547, hardfork_name="istanbul"):
    """Run ganache daemon on the background.

    https://stackoverflow.com/a/8375012/2402577
    """
    print(f"## Launching ganache-cli on port={port}")
    cmd = [
        "ganache-cli",
        "--server.port",
        port,
        "--chain.hardfork",
        hardfork_name,
        "--miner.blockGasLimit",
        "6721975",
        "--wallet.totalAccounts",
        "10",
        # "--blockTime",
        # cfg.BLOCK_DURATION,
        "--chain.allowUnlimitedContractSize",
    ]
    cmd_str = " ".join(str(t) for t in cmd)
    print(cmd_str)
    with daemon.DaemonContext():
        popen_communicate(cmd, env.GANACHE_LOG)


def main():
    if len(sys.argv) == 2:
        port = int(sys.argv[1])

    if not is_ganache_on(8547):
        run(port)


if __name__ == "__main__":
    main()
