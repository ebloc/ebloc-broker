#!/usr/bin/env python3

import sys
from pathlib import Path

from broker import cfg
from broker._utils import _log
from broker._utils._log import _console_clear, console_ruler
from broker._utils.tools import log, print_tb
from broker.utils import bytes32_to_ipfs

Ebb = cfg.Ebb
print_only_ipfs_result_hashes = False


def watch(eth_address="", from_block=None):
    from_block = 15867616
    if not eth_address:
        log("E: eth_address is empty, run as: [m]./watch.py <eth_address>")
        sys.exit(1)

    if not from_block:
        from_block = Ebb.get_block_number() - cfg.ONE_DAY_BLOCK_DURATION

    is_provider = True
    watch_fn = Path.home() / ".ebloc-broker" / f"job_infos_{eth_address}.out"
    _log.ll.LOG_FILENAME = watch_fn
    if not print_only_ipfs_result_hashes:
        _console_clear()

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

    for idx, job in enumerate(event_filter.get_all_entries()):
        try:
            _args = job["args"]
        except:
            job = job[1]
            _args = job["args"]

        if idx != 0:
            console_ruler()

        _job = Ebb.get_job_info(
            _args["provider"],
            _args["jobKey"],
            _args["index"],
            0,
            job["blockNumber"],
            is_print=False,
            is_log_print=not print_only_ipfs_result_hashes,
        )
        del _job["code_hashes"]
        if _job["result_ipfs_hash"] in (b"", ""):
            del _job["result_ipfs_hash"]

        if print_only_ipfs_result_hashes:
            if "result_ipfs_hash" in _job:
                log(bytes32_to_ipfs(_job["result_ipfs_hash"]))
                # log(f"{_job['job_key']} {_job['index']} {result_ipfs_hash}")
        # else:
        #     log(_job)


def main():
    eth_address = None
    if len(sys.argv) == 2:
        eth_address = sys.argv[1]

    watch(eth_address)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        print_tb(e)
