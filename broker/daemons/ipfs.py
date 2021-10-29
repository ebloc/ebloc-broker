#!/usr/bin/env python3

import sys
from pathlib import Path

import daemon

import broker.cfg as cfg
import broker.config as config
from broker._utils.tools import print_tb
from broker.utils import is_ipfs_on, log, popen_communicate


def run():
    """Run the daemon.

    __ https://stackoverflow.com/a/8375012/2402577
    """
    log("==> Running ipfs daemon")
    with daemon.DaemonContext():
        cmd = ["/usr/local/bin/ipfs", "daemon"]  # , "--mount"]
        _env = {"LIBP2P_FORCE_PNET": "1", "IPFS_PATH": Path.home().joinpath(".ipfs")}
        p, output, error = popen_communicate(cmd=cmd, stdout_file=config.env.IPFS_LOG, _env=_env)

    # ipfs mounted at: /ipfs
    # output = run(["sudo", "ipfs", "mount", "-f", "/ipfs"])
    # logging.info(output)
    #
    # for home and home2
    # ipfs swarm connect /ip4/192.168.1.3/tcp/4001/p2p/12D3KooWSE6pY7t5NxMLiGd4h7oba6XqxJFD2KNZTQFEjWLeHKsd


if __name__ == "__main__":
    try:
        config.env = config.ENV()
    except Exception as e:
        print_tb(e)
        log("E: env.IPFS_LOG is not set")
        sys.exit(1)

    if not is_ipfs_on():
        cfg.ipfs.remove_lock_files()
        run()
