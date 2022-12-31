#!/usr/bin/env python3

import sys
from pathlib import Path

from broker import cfg
from broker._utils import _log
from broker._utils._log import _console_clear, console_ruler
from broker._utils.tools import log, print_tb
from broker.lib import state
from broker.utils import bytes32_to_ipfs

Ebb = cfg.Ebb
is_print_only_ipfs_result_hashes = True
is_compact = True  # to get the workload type


def watch(eth_address="", from_block=None):
    """Log submitted jobs' information."""
    from_block = 18813273
    if not eth_address:
        log("E: eth_address is empty, run as: [m]./watch.py <eth_address>")
        sys.exit(1)

    if not from_block:
        from_block = Ebb.get_block_number() - cfg.ONE_DAY_BLOCK_DURATION

    is_provider = True
    watch_fn = Path.home() / ".ebloc-broker" / f"jobs_info_{eth_address}.out"
    _log.ll.LOG_FILENAME = watch_fn
    open(watch_fn, "w").close()  # clean the file
    if not is_print_only_ipfs_result_hashes:
        _console_clear()

    if is_provider:
        _argument_filters = {"provider": eth_address}
    else:
        _argument_filters = {"owner": eth_address}

    event_filter = Ebb._eblocbroker.events.LogJob.createFilter(
        fromBlock=int(from_block),
        argument_filters=_argument_filters,
        toBlock="latest",
    )
    completed_count = 0
    job_count = 0
    for job in event_filter.get_all_entries():
        job_count += 1
        try:
            _args = job["args"]
        except:
            job = job[1]
            _args = job["args"]

        # if idx != 0:
        #     console_ruler()

        _job = Ebb.get_job_info(
            _args["provider"],
            _args["jobKey"],
            _args["index"],
            0,
            job["blockNumber"],
            is_print=False,
            is_log_print=not is_print_only_ipfs_result_hashes and not is_compact,
            is_fetch_code_hashes=is_compact,
        )
        if is_compact:
            # log(_job["code_hashes"])  # log
            state_val = state.inv_code[_job["stateCode"]]
            if state_val == "COMPLETED":
                completed_count += 1

            log(f"* {_job['job_key']} {_job['index']} {state_val}", end="")

        # breakpoint()  # DEBUG
        del _job["code_hashes"]
        if _job["result_ipfs_hash"] in (b"", ""):
            del _job["result_ipfs_hash"]

        if is_print_only_ipfs_result_hashes:
            if "result_ipfs_hash" in _job:
                _ipfs_hash = bytes32_to_ipfs(_job["result_ipfs_hash"])
                log(f" result_ipfs_hash={_ipfs_hash}")
                # log(f"{_job['job_key']} {_job['index']} {result_ipfs_hash}")
            else:
                log()
        else:
            log()

        # else:
        #     log(_job)

    log(f"{completed_count}/{job_count}")


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
