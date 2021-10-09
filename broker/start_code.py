#!/usr/bin/env python3

from broker._utils._log import log
import broker._utils._log as _log
from subprocess import PIPE, Popen, check_output
import sys
import time
from datetime import datetime
from broker.config import env
import broker.cfg as cfg


def start_call(job_key, index, slurm_job_id):
    """Run when slurm job launches.

    cmd1: scontrol show job slurm_job_id | \
             grep 'StartTime'| grep -o -P '(?<=StartTime=).*(?= E)'

    cmd2: date -d 2018-09-09T18:38:29 +"%s"
    """
    Ebb = cfg.Ebb
    _log.ll.LOG_FILENAME = f"{env.LOG_PATH}/transactions/{env.PROVIDER_ID}_{index}.txt"
    _log.ll.IS_PRINT = False
    log(f"~/ebloc-broker/broker/start_code.py {job_key} {index} {slurm_job_id}")
    job_id = 0  # TODO: should be obtained from the user's input
    p1 = Popen(["scontrol", "show", "job", slurm_job_id], stdout=PIPE)
    p2 = Popen(["grep", "StartTime"], stdin=p1.stdout, stdout=PIPE)
    p1.stdout.close()
    p3 = Popen(
        ["grep", "-o", "-P", "(?<=StartTime=).*(?= E)"],
        stdin=p2.stdout,
        stdout=PIPE,
    )
    p2.stdout.close()
    date = p3.communicate()[0].decode("utf-8").strip()
    start_time = check_output(["date", "-d", date, "+'%s'"]).strip().decode("utf-8").strip("'")
    log(f"{env.EBLOCPATH}/broker/eblocbroker/set_job_status_running.py "
        f"{job_key} {index} {job_id} {start_time}")
    for attempt in range(10):
        if attempt > 0:
            log(f"Warning: sleeping for {env.BLOCK_DURATION * 2}...")
            time.sleep(env.BLOCK_DURATION * 2)

        try:
            tx = Ebb.set_job_status_running(job_key, index, job_id, start_time)
            tx_hash = Ebb.tx_id(tx)
            d = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log(f"tx_hash={tx_hash}", "bold")
            log(f"==> set_job_status_running_started {start_time} | attempt_date={d}")
            return
        except Exception as e:
            log(f"attempt={attempt} {e}")
            if "Execution reverted" in str(e):
                log(f"Warning: {e}")
                sys.exit(1)

            if "Transaction with the same hash was already imported." in str(e):
                log(f"Warning: {e}")
                sys.exit(1)

            if "If you wish to broadcast, include `allow_revert:True`" in str(e):
                log(f"Warning: {e}")
                sys.exit(1)

    log("E: start_code.py failed at all the attempts, abort")
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        log("E: Wrong number of arguments")
    else:
        start_call(sys.argv[1], sys.argv[2], sys.argv[3])
