#!/usr/bin/env python3

"""Guide asynchronous polling.

__ http://web3py.readthedocs.io/en/latest/filters.html#examples-listening-for-events
"""

import datetime
import sys
import time
from contextlib import suppress

from broker import cfg
from broker._utils._log import Style, br, console_ruler
from broker._utils.tools import log
from broker.utils import CacheType, StorageID, bytes32_to_ipfs


def handle_event(logged_jobs):
    for job in logged_jobs:
        cloud_storage_id = job.args["cloudStorageID"]
        """
        if StorageID.IPFS == cloud_storage_id or cloudStorageID.IPFS_GPG == cloud_storage_id:
            jobKey = bytes32_to_ipfs(logged_jobs[i].args['jobKey'])
        else:
            jobKey = logged_jobs[i].args['jobKey']
        """
        log(f"transaction_hash={job['transactionHash'].hex()} | log_index={job['logIndex']}")
        log(f"block_number={job['blockNumber']}")
        log(f"provider={job.args['provider']}")
        log(f"job_key={job.args['jobKey']}")
        log(f"index={job.args['index']}")
        log(f"cloud_storage_id={StorageID(cloud_storage_id).name}")
        log(f"cache_type={CacheType(job.args['cacheType'].name)}")
        log(f"received={job.args['received']}")
        for value in job.args["sourceCodeHash"]:
            sourceCodeHash = job.args["sourceCodeHash"][value]
            log(f"code_hash{br(value)} => {bytes32_to_ipfs(sourceCodeHash)}")

        console_ruler()


def log_loop(event_filter, poll_interval: int = 2):
    """Return triggered job event.

    SIGALRM(14) Term Timer signal from alarm(2).  Note: This is by design; see
    PEP 475, and the documentation
    <https://docs.python.org/3.5/library/time.html#time.sleep>.

    If you make your signal handler raise an exception, it will interrupt the
    sleep() call most of the time.  But if the signal happens to be received
    just before the sleep() call is about to be entered, the handler will only
    be run when the underlying OS sleep() call returns 10 s later.
    """
    sleep_duration = 0
    while True:
        block_num = cfg.Ebb.get_block_number()
        since_time = datetime.timedelta(seconds=sleep_duration)
        sys.stdout.write(
            f"\r{Style.GREENB}##{Style.END} {Style.B}[{Style.E}"
            f"{Style.YELLOWB}block_num{Style.END}={Style.CYANB}{block_num}{Style.END}{Style.B}]{Style.E} "
            f"waiting events for jobs since {Style.CYANB}{since_time}{Style.END} "
        )
        sys.stdout.flush()
        logged_jobs = event_filter.get_new_entries()
        if len(logged_jobs) > 0:
            log()
            return logged_jobs

        sleep_duration += poll_interval
        with suppress(Exception):
            # may end up in handler() at _utils/tools.py
            time.sleep(poll_interval)


def run_log_job(self, from_block, provider):
    event_filter = self._eblocbroker.events.LogJob.createFilter(
        fromBlock=int(from_block),
        toBlock="latest",
        argument_filters={"provider": str(provider)},
    )
    logged_jobs = event_filter.get_all_entries()
    if len(logged_jobs) > 0:
        return logged_jobs
    else:
        return log_loop(event_filter)


def run_log_cancel_refund(self, from_block, provider):
    event_filter = self._eblocbroker.events.LogRefund.createFilter(
        fromBlock=int(from_block), argument_filters={"provider": str(provider)}
    )
    logged_cancelled_jobs = event_filter.get_all_entries()
    if len(logged_cancelled_jobs) > 0:
        return logged_cancelled_jobs
    else:
        return log_loop(event_filter)


def main():
    Ebb = cfg.Ebb
    if len(sys.argv) == 3:
        from_block = int(sys.argv[1])
        provider = str(sys.argv[2])  # Only obtains jobs that are submitted to the provider.
    else:
        from_block = 15867616
        provider = "0x1926b36af775e1312fdebcc46303ecae50d945af"

    handle_event(logged_jobs=Ebb.run_log_job(from_block, provider))


if __name__ == "__main__":
    main()

"""
bytes32[] sourceCodeHash,
uint8 cacheType,
uint received);

def run_single_log_job(self, from_block, jobKey, transactionHash):
    event_filter = self._eblocbroker.events.LogJob.createFilter(
        fromBlock=int(from_block), argument_filters={"provider": str(provider)}
    )
    logged_jobs = event_filter.get_all_entries()

    if len(logged_jobs) > 0:
        for logged_job in logged_jobs:
            if logged_job["transactionHash"].hex() == transactionHash:
                return logged_job["index"]
    else:
        return log_loop(event_filter, 2)

"""
