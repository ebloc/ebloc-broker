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
        while True:
            job_id = 0
            job_state = job.Ebb.get_job_state(job.info["provider"], job.info["jobKey"], job.info["index"], job_id)
            state_val = state.inv_code[job_state]
            log(
                f"* job={job.info['jobKey']} index={job.info['index']} {state_val} {_date()}\t\t\t",
                is_write=False,
                end="\r",
            )
            if state_val == "COMPLETED":
                break

            time.sleep(2)

        log(f"* job={job.info['jobKey']} {state_val} {_date()}\t")


if __name__ == "__main__":
    try:
        job0 = Job()
        yaml_fn = Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job_without_data.yaml"
        job0.set_config(yaml_fn)
        submit_ipfs(job0)

        job1 = Job()
        yaml_fn = Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job_without_data.yaml"
        job1.set_config(yaml_fn)
        submit_ipfs(job1)

        jobs_to_wait = [job0, job1]
        wait_till_job_is_completed(jobs_to_wait)

        job = Job()
        yaml_fn = Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job_without_data.yaml"
        job.set_config(yaml_fn)
        submit_ipfs(job)
        log(ok(no_space=True))
    except KeyboardInterrupt:
        pass
    except QuietExit as e:
        print(f"#> {e}")
    except Exception as e:
        print_tb(str(e))
