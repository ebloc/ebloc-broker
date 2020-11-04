#!/usr/bin/env python3

import subprocess
import sys
import time
from datetime import datetime

import eblocbroker.Contract as Contract
from config import env


def start_call(job_key, index, slurm_job_id):
    Ebb = Contract.eblocbroker
    job_id = 0  # TODO: should be obtained from the user's input
    # cmd: scontrol show job slurm_job_id | grep 'StartTime'| grep -o -P '(?<=StartTime=).*(?= E)'
    p1 = subprocess.Popen(["scontrol", "show", "job", slurm_job_id], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "StartTime"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["grep", "-o", "-P", "(?<=StartTime=).*(?= E)"], stdin=p2.stdout, stdout=subprocess.PIPE,)
    p2.stdout.close()
    date = p3.communicate()[0].decode("utf-8").strip()
    # cmd: date -d 2018-09-09T18:38:29 +"%s"
    start_time = subprocess.check_output(["date", "-d", date, "+'%s'"]).strip().decode("utf-8").strip("'")

    env.log_filename = f"{env.LOG_PATH}/transactions/{env.PROVIDER_ID}.txt"
    f = open(env.log_filename, "a")
    f.write(f"\n{env.EBLOCPATH}/eblocbroker/set_job_status_running.py {job_key} {index} {job_id} {start_time}\n")
    time.sleep(.25)
    for attempt in range(2):
        if attempt > 0:
            time.sleep(env.BLOCK_DURATION)
        try:
            tx_hash = Ebb.set_job_status_running(job_key, index, job_id, start_time)
            break
        except:
            f.write(f"try={attempt}")
    else:  # we failed all the attempts - abort
        f.write("\n")
        f.close()
        sys.exit(1)

    d = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write(f"{job_key}_{index} | tx_hash={tx_hash} | set_job_status_running_started {start_time}\n")
    f.write(f"start_time={start_time}  {d}]\n")
    f.close()


if __name__ == "__main__":
    job_key = sys.argv[1]
    index = sys.argv[2]
    slurm_job_id = sys.argv[3]
    start_call(job_key, index, slurm_job_id)
