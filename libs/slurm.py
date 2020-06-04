#!/usr/bin/env python3
import subprocess
import sys
import time

from config import logging
from lib import run
from utils import _colorize_traceback, popen_communicate


def add_user_to_slurm(user):
    # remove__user(user)
    cmd = ["sacctmgr", "add", "account", user, "--immediate"]
    p, output, *_ = popen_communicate(cmd)
    if p.returncode != 0 and "Nothing new added" not in output:
        _colorize_traceback()
        logging.error(f"E: sacctmgr remove error: {output}")
        raise

    try:
        if "Nothing new added" not in output:
            run(["sacctmgr", "create", "user", user, f"defaultaccount={user}", "adminlevel=[None]", "--immediate"])
    except Exception as e:
        raise Exception("E: Problem on sacctmgr create user") from e


def remove_user(user):
    cmd = ["sacctmgr", "remove", "user", "where", f"user={user}", "--immediate"]
    p, output, *_ = popen_communicate(cmd)
    if p.returncode and "Nothing deleted" not in output:
        logging.error(f"E: sacctmgr remove error: {output}")
        raise


def get_idle_cores(is_print_flag=True):
    core_info = run(["sinfo", "-h", "-o%C"]).split("/")
    if len(core_info) != 0:
        allocated_cores = core_info[0]
        idle_cores = core_info[1]
        other_cores = core_info[2]
        total_cores = core_info[3]
        if is_print_flag:
            logging.info(
                f"AllocatedCores={allocated_cores} |"
                f"IdleCores={idle_cores} |"
                f"OtherCores={other_cores} |"
                f"TotalNumberOfCores={total_cores}"
            )
    else:
        logging.error("sinfo is emptry string")
        idle_cores = None

    return idle_cores


def pending_jobs_check():
    """If there is no idle cores, waits for idle cores to be emerged."""
    idle_cores = get_idle_cores()
    is_print_flag = 0
    while idle_cores is None:
        if not is_print_flag:
            logging.info("Waiting running jobs to be completed...")
            is_print_flag = 1
        idle_cores = get_idle_cores(is_print_flag=False)
        time.sleep(10)


def is_on() -> bool:
    """Checks whether Slurm runs on the background or not, if not runs slurm."""
    logging.info("Checking Slurm... ")
    output = run(["sinfo"])
    if "PARTITION" not in output:
        logging.error("E: sinfo returns emprty string, please run:\nsudo ./bash_scripts/run_slurm.sh\n")
        if not output:
            logging.error(f"E: {output}")

        logging.info("Starting Slurm... \n")
        subprocess.run(["sudo", "bash", "bash_scripts/run_slurm.sh"])
        return False
    elif "sinfo: error" in output:
        logging.error(f"Error on munged: \n {output} \n run:\nsudo munged -f \n" "/etc/init.d/munge start")
        return False
    else:
        logging.info("Done")
        return True


def get_elapsed_raw_time(slurm_job_id) -> int:
    try:
        cmd = ["sacct", "-n", "-X", "-j", slurm_job_id, "--format=Elapsed"]
        elapsed_time = run(cmd)
    except:
        sys.exit(1)

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
    logging.info(f"elapsed_raw_time={elapsed_raw_time}")
    return elapsed_raw_time


def get_job_end_time(slurm_job_id):
    # cmd: scontrol show job slurm_job_id | grep 'EndTime'| grep -o -P '(?<=EndTime=).*(?= )'
    try:
        output = run(["scontrol", "show", "job", slurm_job_id])
    except:
        sys.exit()
    p1 = subprocess.Popen(["echo", output], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "EndTime"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["grep", "-o", "-P", "(?<=EndTime=).*(?= )"], stdin=p2.stdout, stdout=subprocess.PIPE,)
    p2.stdout.close()
    date = p3.communicate()[0].decode("utf-8").strip()

    cmd = ["date", "-d", date, "+'%s'"]  # cmd: date -d 2018-09-09T21:50:51 +"%s"
    try:
        end_time_stamp = run(cmd)
    except:
        sys.exit()
    end_time_stamp = end_time_stamp.rstrip().replace("'", "")
    logging.info(f"end_time_stamp={end_time_stamp}")
    return end_time_stamp
