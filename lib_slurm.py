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


def slurm_pending_jobs_check():
    """ If there is no idle cores, waits for idle cores to be emerged. """
    idle_cores = get_idle_cores()
    is_print_flag = 0
    while idle_cores is None:
        if is_print_flag == 0:
            logging.info("Waiting running jobs to be completed...")
            is_print_flag = 1

        time.sleep(10)
        idle_cores = get_idle_cores(False)


def is_slurm_on() -> bool:
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
