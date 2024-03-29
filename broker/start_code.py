#!/usr/bin/env python3

import os
import sys
import time
from datetime import datetime
from subprocess import PIPE, Popen, check_output

from broker import cfg
from broker._utils import _log
from broker._utils._log import br, log, ok
from broker.config import env
from broker.lib import state
from broker.utils import popen_communicate


def start_call(key, index, jobid, slurm_job_id, sleep_dur=0) -> None:
    """Run when slurm job launches.

    * cmd1:
    scontrol show job slurm_job_id | \
        grep 'StartTime'| grep -o -P '(?<=StartTime=).*(?= E)'

    * cmd2: date -d 2018-09-09T18:38:29 +"%s"
    """
    if sleep_dur:
        time.sleep(sleep_dur)

    Ebb = cfg.Ebb
    pid = os.getpid()
    #: save pid of the process as soon as possible
    Ebb.mongo_broker.set_job_state_pid(str(key), int(index), pid)
    _log.ll.LOG_FILENAME = env.LOG_DIR / "transactions" / env.PROVIDER_ID.lower() / f"{key}_{index}_{jobid}.txt"
    # _log.ll.IS_PRINT = False
    log(f"~/ebloc-broker/broker/start_code.py {key} {index} {jobid} {slurm_job_id}", "info")
    _, _, error = popen_communicate(["scontrol", "show", "job", slurm_job_id])
    if "slurm_load_jobs error: Invalid job id specified" in str(error):
        log(f"E: {error}")
        sys.exit(1)

    p1 = Popen(["scontrol", "show", "job", slurm_job_id], stdout=PIPE)
    p2 = Popen(["grep", "StartTime"], stdin=p1.stdout, stdout=PIPE)
    p1.stdout.close()  # type: ignore
    p3 = Popen(
        ["grep", "-o", "-P", "(?<=StartTime=).*(?= E)"],
        stdin=p2.stdout,
        stdout=PIPE,
    )
    p2.stdout.close()  # type: ignore
    date = p3.communicate()[0].decode("utf-8").strip()
    start_ts = check_output(["date", "-d", date, "+'%s'"]).strip().decode("utf-8").strip("'")
    log(f"{env.EBB_SCRIPTS}/set_job_state_running.py {key} {index} {jobid} {start_ts}", is_code=True)
    log(f"==> date={datetime.today().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"==> pid={pid}")
    for attempt in range(5):
        if attempt > 0:
            log(f"warning: Sleeping for {cfg.BLOCK_DURATION * 2} ...")
            time.sleep(cfg.BLOCK_DURATION * 2)

        job, *_ = Ebb._get_job_info(env.PROVIDER_ID, key, int(index), int(jobid))
        state_code = int(job[0])
        if state_code > 1:
            log(f"warning: State have already changed state_code={state.inv_code[state_code]}({state_code})")
            sys.exit(0)

        try:
            tx = Ebb.set_job_state_running(key, index, jobid, start_ts)
            tx_hash = Ebb.tx_id(tx)
            log(f"tx_hash={tx_hash}")
            d = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log(f"==> set_job_state_running_started {start_ts} | attempt_date={d}")
            log("==> mongo.set_job_state_running_tx", end="")
            if Ebb.mongo_broker.set_job_state_running_tx(str(key), int(index), str(tx_hash)):
                log(ok())
            else:
                log(br("FAILED"))

            return
        except Exception as e:
            if (
                "Execution reverted" in str(e)
                or "Transaction with the same hash was already imported" in str(e)
                or "If you wish to broadcast, include `allow_revert:True`" in str(e)
            ):
                log(f"warning: {e}")
                sys.exit(1)

            log(f"==> attempt={attempt}: {e}")

    log("E: all the attempts for the start_code() function is failed  [  [red]ABORT[/red]  ]")
    sys.exit(1)


def main():
    if len(sys.argv) == 5:
        start_call(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    elif len(sys.argv) == 6:
        start_call(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        log("E: Wrong number of arguments provided")


if __name__ == "__main__":
    main()
