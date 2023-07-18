#!/usr/bin/env python3

import time
from pathlib import Path
from broker.utils import bytes32_to_ipfs
from broker._utils._log import log, ok
from broker._utils.tools import _date, print_tb
from broker.eblocbroker_scripts.job import Job
from broker.errors import QuietExit
from broker.ipfs.submit import submit_ipfs
from broker.lib import state
from broker import cfg

Ebb = cfg.Ebb


def wait_till_job_is_completed(jobs):
    for job in jobs:
        provider = job.info["provider"]
        key = job.info["jobKey"]
        index = job.info["index"]
        log(f"* job={job.info['jobKey']} index={job.info['index']}")
        flag = False
        while True:
            completed_job_counter = 0
            if flag:
                log("", end="\r")

            log(f"<{_date()}> ", end="")
            for _job_id, _ in enumerate(job.cores):
                job_state = job.Ebb.get_job_state(provider, key, index, _job_id)
                state_val = state.inv_code[job_state]
                log(f"{_job_id}={state_val} ", is_write=False, end="")
                flag = True
                if state_val == "COMPLETED":
                    completed_job_counter += 1
                # else:
                #     time.sleep(15)
                #     break

            if completed_job_counter == len(job.cores):
                break
            else:
                time.sleep(15)

        log(f"* job={job.info['jobKey']} {state_val} {_date()}\t")


def set_patch_results(jobs):
    for job in jobs:
        provider = job.info["provider"]
        key = job.info["jobKey"]
        index = job.info["index"]
        job_id = 0
        output = Ebb.get_job_info(provider, key, index, job_id)
        ipfs_hash = output["result_ipfs_hash"]
        job.patch_ipfs_hash = bytes32_to_ipfs(ipfs_hash)  # QmWWyWXL1kwYYVHq5zrhSQp9GuAV2bKKGeA8LCyRkdzMfk


def get_input_files(jobs):
    input_files_list = []
    for job in jobs:
        input_files_list += job.patch_ipfs_hash

    return input_files_list


def main():
    job0 = Job()
    yaml_fn = Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job_workflow.yaml"
    job0.set_config(yaml_fn)
    submit_ipfs(job0)
    job0.get_generated_output_files()  # fill in

    # job1 = Job()
    # yaml_fn = Path.home() / "ebloc-broker" / "broker" / "ipfs" / "job_workflow.yaml"
    # job1.set_config(yaml_fn)
    # submit_ipfs(job1)

    jobs_to_wait = [job0]
    # jobs_to_wait = [job0, job1]
    wait_till_job_is_completed(jobs_to_wait)
    set_patch_results(jobs_to_wait)

    job2 = Job()
    # job2.input_files = get_input_files([job0, job1])  # job2.input_files = [job0.patch_ipfs_hash, job1.patch_ipfs_hash]

    job2.input_files = ["QmWWyWXL1kwYYVHq5zrhSQp9GuAV2bKKGeA8LCyRkdzMfk"]
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
        print(e)
        print_tb(str(e))
