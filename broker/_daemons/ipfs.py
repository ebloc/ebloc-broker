#!/usr/bin/env python3

import os
import sys
from pathlib import Path

import daemon

from broker import cfg, config
from broker._utils._log import ok
from broker._utils.tools import print_tb
from broker.utils import is_ipfs_on, log, popen_communicate


def run():
    """Run ipfs daemon.

    cmd: ipfs daemon  # --mount
    __ https://stackoverflow.com/a/8375012/2402577
    __ https://gist.github.com/SomajitDey/25f2f7f2aae8ef722f77a7e9ea40cc7c#gistcomment-4022998
    """
    IPFS_BIN = "/usr/local/bin/ipfs"
    ipfs_init_folder = Path.home().joinpath(".ipfs")
    log("#> Running [green]IPFS[/green] daemon")
    if not os.path.isfile(config.env.IPFS_LOG):
        open(config.env.IPFS_LOG, "a").close()

    with daemon.DaemonContext():
        if cfg.IS_PRIVATE_IPFS:
            env = {"LIBP2P_FORCE_PNET": "1", "IPFS_PATH": ipfs_init_folder}
        else:
            env = {"IPFS_PATH": ipfs_init_folder}

        popen_communicate([IPFS_BIN, "daemon", "--routing=none"], stdout_fn=config.env.IPFS_LOG, env=env)

    # ipfs mounted at: /ipfs
    # output = run(["sudo", "ipfs", "mount", "-f", "/ipfs"])
    # log(output)
    #
    # for home and home2
    # ipfs swarm connect /ip4/192.168.1.3/tcp/4001/p2p/12D3KooWSE6pY7t5NxMLiGd4h7oba6XqxJFD2KNZTQFEjWLeHKsd


def main():
    try:
        config.env = config.ENV()
    except Exception as e:
        print_tb(e)
        log("E: env.IPFS_LOG is not set")
        sys.exit(1)

    if not is_ipfs_on():
        cfg.ipfs.remove_lock_files()
        run()
    else:
        log(f"## [green]IPFS[/green] daemon is already running {ok()}")
        sys.exit(100)


if __name__ == "__main__":
    main()
