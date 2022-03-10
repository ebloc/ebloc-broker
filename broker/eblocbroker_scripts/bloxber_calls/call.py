#!/usr/bin/env python3

import os
import sys
import time
from ast import literal_eval as make_tuple

from broker import cfg
from broker._utils._log import br, log
from broker.env import ENV_BASE
from broker.utils import ipfs_to_bytes32


def print_msg(msg):
    """Print arguments."""
    log(f"{br(time.ctime())}, pid: {os.getpid()}] --- {msg}")


def main(*args):
    env = ENV_BASE()
    from brownie import network, project

    _args = make_tuple(str(args))
    network.connect("bloxberg")
    project = project.load(env.CONTRACT_PROJECT_PATH)
    ebb = project.eBlocBroker.at(env.CONTRACT_ADDRESS)
    provider = _args[0]
    job_requester = _args[1]
    job_requester = cfg.w3.toChecksumAddress(job_requester)
    try:
        source_code_hash = ipfs_to_bytes32(_args[2])
    except:
        source_code_hash = _args[2].encode("utf-8")

    try:
        output = ebb.getReceivedStorageDeposit(provider, job_requester, source_code_hash)
    except:
        print("0")  # if its the first submitted job for the user

    try:
        output = ebb.getStorageDuration(provider, source_code_hash)
        print(output)
    except:
        print("(0, 0, False, False)")

    sys.exit(0)


if __name__ == "__main__":
    func_name = sys.argv[1]
    main(*sys.argv[2:])
