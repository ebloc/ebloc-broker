#!/usr/bin/env python3

import os
import sys
import time
from ast import literal_eval as make_tuple

import broker.config as config
from broker.utils import ipfs_to_bytes32


def print_msg(msg):
    """Print arguments."""
    print(f"[{time.ctime()}, pid: {os.getpid()}] --- {msg}")


def main(function_name, *args):
    from brownie import network, project, web3

    config.w3 = web3
    _args = make_tuple(str(args))
    network.connect("bloxberg")
    project = project.load("/mnt/hgfs/ebloc-broker/contract")
    ebb = project.eBlocBroker.at("0xccD25f5Ae21037a6DCCff829B01034E2fD332796")
    job_provider = _args[0]
    job_requester = _args[1]
    source_code_hash = ipfs_to_bytes32(_args[2])
    ops = {"from": job_provider}
    output = ebb.getReceivedStorageDeposit(job_provider, job_requester, source_code_hash, ops)
    print(output)
    output = ebb.getJobStorageTime(job_provider, source_code_hash, ops)
    print(output)
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(*sys.argv[1:])
    else:
        main(*sys.argv[1:])