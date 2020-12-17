#!/usr/bin/env python3

import os
import sys
import time
from ast import literal_eval as make_tuple

from broker._utils._log import br, log
from broker.config import env
from broker.utils import ipfs_to_bytes32


def print_msg(msg):
    """Print arguments."""
    log(f"{br(time.ctime())}, pid: {os.getpid()}] --- {msg}")


def main(*args):
    from brownie import network, project

    _args = make_tuple(str(args))
    network.connect("bloxberg")
    project = project.load(env.CONTRACT_PROJECT_PATH)
    ebb = project.eBlocBroker.at("0xccD25f5Ae21037a6DCCff829B01034E2fD332796")
    job_provider = _args[0]
    job_requester = _args[1]

    try:
        source_code_hash = ipfs_to_bytes32(_args[2])
    except:
        source_code_hash = _args[2].encode("utf-8")

    ops = {"from": job_provider}
    output = ebb.getReceivedStorageDeposit(job_provider, job_requester, source_code_hash, ops)
    print(output)
    output = ebb.getJobStorageTime(job_provider, source_code_hash, ops)
    print(output)
    sys.exit(0)


if __name__ == "__main__":
    func_name = sys.argv[1]
    main(*sys.argv[2:])
