#!/usr/bin/env python3

import sys
from pathlib import Path

from broker import cfg
from broker._utils import _log
from broker._utils._log import _console_clear
from broker._utils.tools import log, print_tb

Ebb = cfg.Ebb
watch_only_jobs = True


def watch(eth_address="", from_block=None):
    from_block = 15394725
    # if not eth_address:
    #     # TODO: pull from cfg
    #     eth_address = "0xeab50158e8e51de21616307a99c9604c1c453a02"

    if not eth_address:
        log("E: eth_address is empty, run as: ./watch.py <eth_address>")
        sys.exit(1)

    if not from_block:
        from_block = Ebb.get_block_number() - cfg.ONE_DAY_BLOCK_DURATION

    is_provider = True
    watch_fn = Path.home() / ".ebloc-broker" / f"watch_{eth_address}.out"
    _log.ll.LOG_FILENAME = watch_fn
    _console_clear()

    if not watch_only_jobs:
        providers_info = {}
        providers = Ebb.get_providers()
        for provider_addr in providers:
            providers_info[provider_addr] = Ebb.get_provider_info(provider_addr)

    if is_provider:
        event_filter = Ebb._eblocbroker.events.LogJob.createFilter(
            fromBlock=int(from_block),
            argument_filters={"provider": eth_address},
            toBlock="latest",
        )
    else:
        event_filter = Ebb._eblocbroker.events.LogJob.createFilter(
            fromBlock=int(from_block),
            argument_filters={"owner": eth_address},
            toBlock="latest",
        )

    for job in enumerate(event_filter.get_all_entries()):
        try:
            _args = job["args"]
        except:
            job = job[1]
            _args = job["args"]

        _job = Ebb.get_job_info(
            _args["provider"],
            _args["jobKey"],
            _args["index"],
            0,
            job["blockNumber"],
            is_print=False,
        )
        log(_job)
        breakpoint()  # DEBUG
        # if _job["result_ipfs_hash"] != empty_bytes32 and _job["result_ipfs_hash"] != "":
        #     result_ipfs_hash = bytes32_to_ipfs(_job["result_ipfs_hash"])
        #     log(result_ipfs_hash)
        #     # log(f"{_job['job_key']} {_job['index']} {result_ipfs_hash}")


if __name__ == "__main__":
    try:
        eth_address = None
        if len(sys.argv) == 2:
            eth_address = sys.argv[1]

        watch(eth_address)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print_tb(e)
