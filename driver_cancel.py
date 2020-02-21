#!/usr/bin/env python3

import hashlib
import subprocess
import time

import lib
from config import load_log
from contractCalls.get_deployed_block_number import get_deployed_block_number
from contractCalls.LogJob import LogJob
from imports import connect_to_web3

w3 = connect_to_web3()
testFlag = False
log_dc = load_log(f"{lib.LOG_PATH}/cancelledJobsLog.out")


with open(lib.CANCEL_BLOCK_READ_FROM_FILE, "r") as content_file:
    cancel_block_read_from_local = content_file.read().strip()

if not cancel_block_read_from_local.isdigit():
    cancel_block_read_from_local = get_deployed_block_number()

log_dc(f"Waiting cancelled jobs from {cancel_block_read_from_local}")
max_val = 0
while True:
    # cancel_block_read_from_local = 2000000 # For test purposes

    # Waits here until new job cancelled into the provider
    logged_jobs_to_process = LogJob.run_log_cancel_refund(cancel_block_read_from_local, lib.PROVIDER_ID)

    for logged_job in logged_jobs_to_process:
        msg_sender = w3.eth.getTransactionReceipt(logged_job["transactionHash"].hex())["from"].lower()
        user_name = hashlib.md5(msg_sender.encode("utf-8")).hexdigest()
        # print(msg_sender)
        # print(logged_job)
        # print(user_name)

        block_number = logged_job["blockNumber"]
        jobKey = logged_job.args["jobKey"]
        index = logged_job.args["index"]
        log_dc(f"block_number={block_number} job_key={jobKey} index={index}")

        if block_number > max_val:
            max_val = block_number

        """
        cmd: sudo su - c6cec9ebdb49fa85449c49251f4a0b9d -c 'jobName=$(echo 200376512531615951349171797788434913951_0/JOB_TO_RUN/200376512531615951349171797788434913951\*0*sh | xargs -n 1 basename); sacct -n -X --format jobid --name $jobName'
        output: 51           231555615+      debug cc6b74f19+          1  COMPLETED      0:0
        """
        res = (
            subprocess.check_output(
                [
                    "sudo",
                    "su",
                    "-",
                    user_name,
                    "-c",
                    f"job_name=$(echo {jobKey}_{index}/JOB_TO_RUN/{jobKey}*{index}*sh"
                    f"| xargs -n 1 basename);"
                    f"sacct -n -X --format jobid --name $job_name",
                ]
            )
            .decode("utf-8")
            .split()
        )
        try:
            jobID = res[0]
            print(f"jobID={jobID}")
            if jobID.isdigit():
                subprocess.run(["scancel", jobID])
                time.sleep(2)  # wait few seconds to cancel the requested job.
                p1 = subprocess.Popen(["scontrol", "show", "job", jobID], stdout=subprocess.PIPE)
                p2 = subprocess.Popen(["grep", "JobState="], stdin=p1.stdout, stdout=subprocess.PIPE)
                p1.stdout.close()
                out = p2.communicate()[0].decode("utf-8").strip()
                if "JobState=CANCELLED" in out:
                    log_dc(f"jobID={jobID} is successfully cancelled.")
                else:
                    log_dc(f"E: jobID={jobID} is not cancelled, something went wrong or already cancelled. {out}")
        except IndexError:
            log_dc("Something went wrong, jobID is returned as None.")

    if int(max_val) != 0:
        value = max_val + 1
        f_blockReadFrom = open(lib.CANCEL_BLOCK_READ_FROM_FILE, "w")  # Updates the latest read block number
        f_blockReadFrom.write(f"{value}")
        f_blockReadFrom.close()
        cancel_block_read_from_local = str(value)
        log_dc("---------------------------------------------")
        log_dc(f"Waiting cancelled jobs from {cancel_block_read_from_local}")
    else:
        currentBlockNumber = block_number()
        f_blockReadFrom = open(lib.CANCEL_BLOCK_READ_FROM_FILE, "w")  # Updates the latest read block number
        f_blockReadFrom.write(f"{currentBlockNumber}")
        f_blockReadFrom.close()
        log_dc("---------------------------------------------")
        log_dc(f"Waiting cancelled jobs from: {currentBlockNumber}")