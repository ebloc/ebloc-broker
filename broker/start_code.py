#!/usr/bin/env python3

import subprocess
import sys
import time
from datetime import datetime

from config import env

import broker.eblocbroker.Contract as Contract


def start_call(job_key, index, slurm_job_id):
    """Run when slurm job launches.

    cmd: date -d 2018-09-09T18:38:29 +"%s"
    """
    Ebb = Contract.ebb()
    job_id = 0  # TODO: should be obtained from the user's input
    # cmd: scontrol show job slurm_job_id | grep 'StartTime'| grep -o -P '(?<=StartTime=).*(?= E)'
    p1 = subprocess.Popen(["scontrol", "show", "job", slurm_job_id], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "StartTime"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(
        ["grep", "-o", "-P", "(?<=StartTime=).*(?= E)"],
        stdin=p2.stdout,
        stdout=subprocess.PIPE,
    )
    p2.stdout.close()
    date = p3.communicate()[0].decode("utf-8").strip()
    start_time = subprocess.check_output(["date", "-d", date, "+'%s'"]).strip().decode("utf-8").strip("'")
    env.log_filename = f"{env.LOG_PATH}/transactions/{env.PROVIDER_ID}.txt"
    f = open(env.log_filename, "a")
    f.write(f"{env.EBLOCPATH}/eblocbroker/set_job_status_running.py {job_key} {index} {job_id} {start_time}\n\n")
    time.sleep(0.5)
    for attempt in range(3):
        if attempt > 0:
            time.sleep(env.BLOCK_DURATION)
        try:
            tx_hash = Ebb.set_job_status_running(job_key, index, job_id, start_time)
            break
        except:
            f.write(f"try={attempt}")
    else:  # failed at all the attempts - abort
        f.write("\n")
        f.close()
        sys.exit(1)

    d = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write(f"{job_key}_{index}\ntx_hash={tx_hash}\nset_job_status_running_started {start_time} {d}\n")
    f.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("E: Wrong number of arguments are provided.")

    start_call(sys.argv[1], sys.argv[2], sys.argv[3])
