#!/usr/bin/env python3

import time
from pathlib import Path

from broker._utils._log import log, ok
from broker._utils.tools import _date, print_tb
from broker.eblocbroker_scripts.job import Job
from broker.errors import QuietExit
from broker.ipfs.submit import submit_ipfs
from broker.lib import state


def wait_till_job_is_completed(jobs):
    for job in jobs:
        provider = job.info["provider"]
        key = job.info["jobKey"]
        index = job.info["index"]
        job_id = 0
        while True:
            job_state = job.Ebb.get_job_state(provider, key, index, job_id)
            state_val = state.inv_code[job_state]
            log(
                f"* job={job.info['jobKey']} index={job.info['index']} {state_val} {_date()}\t\t\t",
                is_write=False,
                end="\r",
            )
            if state_val == "COMPLETED":
                break

            time.sleep(15)

        log(f"* job={job.info['jobKey']} {state_val} {_date()}\t")


def main():
    job0 = Job()
    yaml_fn = Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job_without_data.yaml"
    job0.set_config(yaml_fn)
    submit_ipfs(job0)
    job0.get_generated_output_files()  ## fill in

    job1 = Job()
    yaml_fn = Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job_without_data.yaml"
    job1.set_config(yaml_fn)
    submit_ipfs(job1)

    jobs_to_wait = [job0, job1]
    wait_till_job_is_completed(jobs_to_wait)

    job2 = Job()
    yaml_fn = Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job_without_data.yaml"
    job2.set_config(yaml_fn)
    submit_ipfs(job2)
    log(ok(no_space=True))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"==> {e}")
    except Exception as e:
        print_tb(str(e))
