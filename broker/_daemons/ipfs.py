#!/usr/bin/env python3

import daemon
import os
import sys
from broker.env import ENV_BASE
from broker import cfg, config
from broker._utils._log import ok
from broker._utils.tools import print_tb, run
from broker.utils import is_ipfs_on, log, popen_communicate, is_docker


_env = ENV_BASE()


def mount_ipfs():
    """Mount ipfs at: /ipfs."""
    log(run(["sudo", "ipfs", "mount", "-f", "/ipfs"]))


def _run():
    """Run IPFS daemon.

    cmd: ipfs daemon --migrate --enable-gc --routing=none  # --mount
    __ https://stackoverflow.com/a/8375012/2402577
    __ https://gist.github.com/SomajitDey/25f2f7f2aae8ef722f77a7e9ea40cc7c#gistcomment-4022998
    """
    IPFS_BIN = "/usr/local/bin/ipfs"
    ipfs_init_folder = _env.IPFS_REPO
    if not os.path.isdir(ipfs_init_folder):
        print(run(["ipfs", "init"]))

    if not os.path.isfile(config.env.IPFS_LOG):
        open(config.env.IPFS_LOG, "a").close()

    with daemon.DaemonContext():
        if cfg.IS_PRIVATE_IPFS:
            env = {"LIBP2P_FORCE_PNET": "1", "IPFS_PATH": ipfs_init_folder}
        else:
            env = {"IPFS_PATH": ipfs_init_folder}

        cmd = [IPFS_BIN, "daemon", "--migrate", "--enable-gc"]
        if not is_docker():
            cmd += ["--routing=none"]

        popen_communicate(cmd, stdout_fn=config.env.IPFS_LOG, env=env)

    # mount_ipfs()


def main():
    try:
        config.env = config.ENV()
    except Exception as e:
        print_tb(e)
        log("E: env.IPFS_LOG is not set")
        sys.exit(1)

    if not is_ipfs_on():
        cfg.ipfs.remove_lock_files()
        _run()
    else:
        log(f"> [g]IPFS[/g] daemon is already running {ok()}")
        sys.exit(100)


if __name__ == "__main__":
    main()
