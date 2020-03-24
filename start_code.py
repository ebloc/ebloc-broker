#!/usr/bin/env python

import subprocess
import sys
import time

import lib
from contractCalls.set_job_status_running import set_job_status_running


def start_call(job_key, index, slurm_job_id):
    job_id = 0  # TODO: should be obtained from the user's input
    # cmd: scontrol show job slurm_job_id | grep 'StartTime'| grep -o -P '(?<=StartTime=).*(?= E)'
    p1 = subprocess.Popen(["scontrol", "show", "job", slurm_job_id], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "StartTime"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["grep", "-o", "-P", "(?<=StartTime=).*(?= E)"], stdin=p2.stdout, stdout=subprocess.PIPE,)
    p2.stdout.close()
    date = p3.communicate()[0].decode("utf-8").strip()
    # cmd: date -d 2018-09-09T18:38:29 +"%s"
    startTime = subprocess.check_output(["date", "-d", date, "+'%s'"]).strip().decode("utf-8").strip("'")

    f = open(f"{lib.LOG_PATH}/transactions/{lib.PROVIDER_ID}.txt", "a")
    f.write(f"{lib.EBLOCPATH}/contractCalls/set_job_status_running.py {job_key} {index} {job_id} {startTime}")
    f.write("\n")
    time.sleep(0.25)
    for attempt in range(1):
        if attempt > 0:
            time.sleep(15)
        success, output = set_job_status_running(job_key, index, job_id, startTime)
        if not success or not output:
            f.write(f"{job_key} {index} {slurm_job_id} | Try={attempt}")
        else:  # success
            break
    else:  # we failed all the attempts - abort
        f.write("\n")
        f.close()
        sys.exit(1)

    f.write(f"{job_key}_{index} | tx_hash={output} | set_job_status_running_started {startTime}")
    f.write("\n")
    f.close()


if __name__ == "__main__":
    job_key = sys.argv[1]
    index = sys.argv[2]
    slurm_job_id = sys.argv[3]

    start_call(job_key, index, slurm_job_id)
