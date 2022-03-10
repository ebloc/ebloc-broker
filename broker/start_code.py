#!/usr/bin/env python3

import sys
import time
from datetime import datetime
from subprocess import PIPE, Popen, check_output

from broker import cfg
from broker._utils import _log
from broker._utils._log import br, log, ok
from broker.config import env
from broker.utils import popen_communicate


def start_call(job_key, index, slurm_job_id):
    """Run when slurm job launches.

    * cmd1:
    scontrol show job slurm_job_id | \
        grep 'StartTime'| grep -o -P '(?<=StartTime=).*(?= E)'

    * cmd2:
    date -d 2018-09-09T18:38:29 +"%s"
    """
    Ebb = cfg.Ebb
    _log.ll.LOG_FILENAME = env.LOG_PATH / "transactions" / env.PROVIDER_ID / f"{job_key}_{index}.txt"
    _log.ll.IS_PRINT = False
    log(f"~/ebloc-broker/broker/start_code.py {job_key} {index} {slurm_job_id}")
    job_id = 0  # TODO: should be obtained from the user's input
    _, _, error = popen_communicate(["scontrol", "show", "job", slurm_job_id])
    if "slurm_load_jobs error: Invalid job id specified" in str(error):
        log(f"E: {error}")
        sys.exit(1)

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
    log(f"{env.EBLOCPATH}/broker/eblocbroker_scripts/set_job_status_running.py {job_key} {index} {job_id} {start_time}")
    for attempt in range(10):
        if attempt > 0:
            log(f"warning: sleeping for {cfg.BLOCK_DURATION * 2} ...")
            time.sleep(cfg.BLOCK_DURATION * 2)

        try:
            tx = Ebb.set_job_status_running(job_key, index, job_id, start_time)
            tx_hash = Ebb.tx_id(tx)
            log(f"tx_hash={tx_hash}", "bold")
            d = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log(f"==> set_job_status_running_started {start_time} | attempt_date={d}")
            log("## mongo.set_job_status_running_tx ", end="")
            if Ebb.mongo_broker.set_job_status_running_tx(str(job_key), int(index), str(tx_hash)):
                log(ok())
            else:
                log(br("FAILED"))

            return
        except Exception as e:
            log(f"## attempt={attempt}: {e}")
            if (
                "Execution reverted" in str(e)
                or "Transaction with the same hash was already imported" in str(e)
                or "If you wish to broadcast, include `allow_revert:True`" in str(e)
            ):
                log(f"warning: {e}")
                sys.exit(1)

    log("E: start_code.py failed at all the attempts, abort")
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        log("E: wrong number of arguments")
    else:
        start_call(sys.argv[1], sys.argv[2], sys.argv[3])
