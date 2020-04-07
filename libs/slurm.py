#!/usr/bin/env python3
import subprocess
import time

from config import logging
from lib import run_command


def get_idle_cores(is_print_flag=True):
    cmd = ["sinfo", "-h", "-o%C"]
    success, core_info = run_command(cmd)
    core_info = core_info.split("/")
    if len(core_info) != 0:
        allocated_cores = core_info[0]
        idle_cores = core_info[1]
        other_cores = core_info[2]
        total_number_of_cores = core_info[3]
        if is_print_flag:
            logging.info(
                f"AllocatedCores={allocated_cores} |IdleCores={idle_cores} |OtherCores={other_cores}| TotalNumberOfCores={total_number_of_cores}"
            )
    else:
        logging.error("sinfo is emptry string.")
        idle_cores = None
    return idle_cores


def pending_jobs_check():
    """ If there is no idle cores, waits for idle cores to be emerged. """
    idle_cores = get_idle_cores()
    is_print_flag = 0
    while idle_cores is None:
        if not is_print_flag:
            logging.info("Waiting running jobs to be completed...")
            is_print_flag = 1
        time.sleep(10)
        idle_cores = get_idle_cores(False)


def is_on() -> bool:
    """Checks whether Slurm runs on the background or not, if not runs slurm"""
    logging.info("Checking Slurm... ")
    success, output = run_command(["sinfo"])
    if "PARTITION" not in output:
        logging.error("E: sinfo returns emprty string, please run:\nsudo ./runSlurm.sh\n")
        if not output:
            logging.error(f"E: {output}")

        logging.info("Starting Slurm... \n")
        subprocess.run(["sudo", "bash", "runSlurm.sh"])
        return False
    elif "sinfo: error" in output:
        logging.error(f"Error on munged: \n {output} \n Run: \n" "sudo munged -f \n" "/etc/init.d/munge start")
        return False
    else:
        logging.info("Done")
        return True


def get_elapsed_raw_time(slurm_job_id) -> int:
    cmd = ["sacct", "-n", "-X", "-j", slurm_job_id, "--format=Elapsed"]
    success, elapsed_time = run_command(cmd, None, True)
    logging.info(f"ElapsedTime={elapsed_time}")
    elapsed_time = elapsed_time.split(":")
    elapsed_day = "0"
    elapsed_hour = elapsed_time[0].strip()
    elapsed_minute = elapsed_time[1].rstrip()
    if "-" in str(elapsed_hour):
        elapsed_hour = elapsed_hour.split("-")
        elapsed_day = elapsed_hour[0]
        elapsed_hour = elapsed_hour[1]

    elapsed_raw_time = int(elapsed_day) * 1440 + int(elapsed_hour) * 60 + int(elapsed_minute) + 1
    logging.info(f"ElapsedRawTime={elapsed_raw_time}")
    return elapsed_raw_time


def get_job_end_time(slurm_job_id):
    # cmd: scontrol show job slurm_job_id | grep 'EndTime'| grep -o -P '(?<=EndTime=).*(?= )'
    success, output = run_command(["scontrol", "show", "job", slurm_job_id], None, True)
    p1 = subprocess.Popen(["echo", output], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "EndTime"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["grep", "-o", "-P", "(?<=EndTime=).*(?= )"], stdin=p2.stdout, stdout=subprocess.PIPE,)
    p2.stdout.close()
    date = p3.communicate()[0].decode("utf-8").strip()

    cmd = ["date", "-d", date, "+'%s'"]  # cmd: date -d 2018-09-09T21:50:51 +"%s"
    success, end_time_stamp = run_command(cmd, None, True)
    end_time_stamp = end_time_stamp.rstrip().replace("'", "")
    logging.info(f"end_time_stamp={end_time_stamp}")
    return end_time_stamp
