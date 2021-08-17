#!/usr/bin/env python3

import time

import broker.config as config
from broker.config import QuietExit, env, logging
from broker.lib import run
from broker.utils import BashCommandsException, _colorize_traceback, is_process_on, log, popen_communicate, print_ok


def add_user_to_slurm(user):
    # remove__user(user)
    cmd = ["sacctmgr", "add", "user", user, f"account={user}", "--immediate"]
    # cmd = ["sacctmgr", "add", "account", user, "--immediate"]
    p, output, *_ = popen_communicate(cmd)
    if p.returncode != 0 and "Nothing new added" not in output:
        _colorize_traceback()
        logging.error(f"E: sacctmgr remove error: {output}")
        raise

    # try:
    #     if "Nothing new added" not in output:
    #         run(["sacctmgr", "create", "user", user, f"defaultaccount={env.SLURMUSER}", "adminlevel=[None]", "--immediate"])
    # except Exception as e:
    #     raise Exception("E: Problem on sacctmgr create user") from e


def remove_user(user):
    cmd = ["sacctmgr", "remove", "user", "where", f"user={user}", "--immediate"]
    p, output, error_msg = popen_communicate(cmd)
    if p.returncode and "Nothing deleted" not in output:
        logging.error(f"E: sacctmgr remove error: {output}")
        raise BashCommandsException(p.returncode, output, error_msg, str(cmd))


def get_idle_cores(is_print_flag=True):
    """Return idle cores.

    https://stackoverflow.com/a/50095154/2402577
    """
    core_info = run(["sinfo", "-h", "-o%C"]).split("/")
    if len(core_info) != 0:
        allocated_cores = core_info[0]
        idle_cores = core_info[1]
        other_cores = core_info[2]
        total_cores = core_info[3]
        if is_print_flag:
            log(
                f"allocated_cores={allocated_cores} |"
                f"idle_cores={idle_cores} |"
                f"other_cores={other_cores} |"
                f"total_number_of_cores={total_cores}",
                "green",
            )
    else:
        logging.error("E: sinfo is emptry string")
        return None
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
    log("## Checking Slurm... ", end="")
    processes = ["\<slurmd\>", "\<slurmdbd\>", "\<slurmctld\>"]
    for process_name in processes:
        if not is_process_on(process_name, process_name, process_count=0, is_print=False):
            log("failed", "red", is_bold=True)
            process_name = process_name.replace("\\", "").replace(">", "").replace("<", "")
            log(
                f"E: {process_name} is not running in the background. Please run:\n"
                f"sudo {env.EBLOCPATH}/broker/bash_scripts/run_slurm.sh",
                "red",
            )
            raise config.QuietExit

    output = run(["sinfo"])
    if "PARTITION" not in output:
        logging.error("E: sinfo returns invalid string. Please run:\nsudo ./bash_scripts/run_slurm.sh\n")
        if not output:
            logging.error(f"E: {output}")
        try:
            logging.info("Starting Slurm... \n")
            run(["sudo", "bash", "bash_scripts/run_slurm.sh"])
            return True
        except:
            return False
    elif "sinfo: error" in output:
        logging.error(f"Error on munged: \n {output}\nrun:\nsudo munged -f \n/etc/init.d/munge start")
        return False
    else:
        print_ok()
        return True


def get_elapsed_time(slurm_job_id) -> int:
    try:
        cmd = ["sacct", "-n", "-X", "-j", slurm_job_id, "--format=Elapsed"]
        elapsed_time = run(cmd)
    except:
        raise QuietExit

    logging.info(f"elapsed_time={elapsed_time}")
    elapsed_time = elapsed_time.split(":")
    elapsed_day = "0"
    elapsed_hour = elapsed_time[0].strip()
    elapsed_minute = elapsed_time[1].rstrip()
    if "-" in str(elapsed_hour):
        elapsed_hour = elapsed_hour.split("-")
        elapsed_day = elapsed_hour[0]
        elapsed_hour = elapsed_hour[1]

    elapsed_time = int(elapsed_day) * 1440 + int(elapsed_hour) * 60 + int(elapsed_minute) + 1
    logging.info(f"elapsed_time={elapsed_time}")
    return elapsed_time


def get_job_end_time(slurm_job_id) -> int:
    """Get the end time of the job in universal time"""
    end_time = run(["sacct", "-n", "-X", "-j", slurm_job_id, "--format=End"])
    if end_time == "":
        log(f"E: slurm_load_jobs error: Invalid job_id ({slurm_job_id}) specified.", "red")
        raise QuietExit

    try:
        # cmd: date -d 2018-09-09T21:50:51 +"%s"
        end_time_stamp = run(["date", "-d", end_time, "+'%s'"])
    except:
        raise QuietExit

    end_time_stamp = end_time_stamp.rstrip().replace("'", "")
    log(f"end_time_stamp={end_time_stamp}", "blue")
    return end_time_stamp
