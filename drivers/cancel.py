#!/usr/bin/env python3

import subprocess
import time

import eblocbroker.Contract as Contract
from config import env, setup_logger
from imports import connect_to_web3
from utils import eth_address_to_md5

w3 = connect_to_web3()
ebb = Contract.eblocbroker
testFlag = False
log_dc = setup_logger(f"{env.LOG_PATH}/cancelledJobsLog.out")


with open(env.CANCEL_BLOCK_READ_FROM_FILE, "r") as content_file:
    cancel_block_read_from_local = content_file.read().strip()

if not cancel_block_read_from_local.isdigit():
    cancel_block_read_from_local = ebb.get_deployed_block_number()

log_dc(f"Waiting cancelled jobs from {cancel_block_read_from_local}")
max_val = 0
while True:
    time.sleep(0.1)
    # cancel_block_read_from_local = 2000000 # for test purposes

    # waits here until new job cancelled into the provider
    logged_jobs_to_process = ebb.LogJob.run_log_cancel_refund(cancel_block_read_from_local, env.PROVIDER_ID)

    for logged_job in logged_jobs_to_process:
        msg_sender = w3.eth.getTransactionReceipt(logged_job["transactionHash"].hex())["from"].lower()
        user_name = eth_address_to_md5(msg_sender)
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
        output = (
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
            job_id = output[0]
            print(f"job_id={job_id}")
            if job_id.isdigit():
                subprocess.run(["scancel", job_id])
                time.sleep(2)  # wait few seconds to cancel the requested job.
                p1 = subprocess.Popen(["scontrol", "show", "job", job_id], stdout=subprocess.PIPE)
                p2 = subprocess.Popen(["grep", "JobState="], stdin=p1.stdout, stdout=subprocess.PIPE)
                p1.stdout.close()
                out = p2.communicate()[0].decode("utf-8").strip()
                if "JobState=CANCELLED" in out:
                    log_dc(f"job_id={job_id} is successfully cancelled.")
                else:
                    log_dc(f"E: job_id={job_id} is not cancelled, something went wrong or already cancelled. {out}")
        except IndexError:
            log_dc("Something went wrong, job_id is returned as None.")

    if int(max_val) != 0:
        value = max_val + 1
        f_blockReadFrom = open(env.CANCEL_BLOCK_READ_FROM_FILE, "w")  # updates the latest read block number
        f_blockReadFrom.write(f"{value}")
        f_blockReadFrom.close()
        cancel_block_read_from_local = str(value)
        log_dc("---------------------------------------------")
        log_dc(f"Waiting cancelled jobs from {cancel_block_read_from_local}")
    else:
        currentBlockNumber = block_number()
        f_blockReadFrom = open(env.CANCEL_BLOCK_READ_FROM_FILE, "w")  # updates the latest read block number
        f_blockReadFrom.write(f"{currentBlockNumber}")
        f_blockReadFrom.close()
        log_dc("---------------------------------------------")
        log_dc(f"Waiting cancelled jobs from: {currentBlockNumber}")
