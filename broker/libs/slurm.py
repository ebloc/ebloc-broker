#!/usr/bin/env python3

import time

from broker._utils._log import ok
from broker._utils.tools import is_process_on
from broker.config import env
from broker.errors import BashCommandsException, QuietExit
from broker.lib import run
from broker.utils import log, popen_communicate, print_tb


def add_user_to_slurm(user):
    #: remove__user(user)
    cmd = ["sacctmgr", "add", "user", user, f"account={user}", "--immediate"]
    # cmd = ["sacctmgr", "add", "account", user, "--immediate"]
    p, output, *_ = popen_communicate(cmd)
    if p.returncode > 0 and "Nothing new added" not in output:
        print_tb()
        raise Exception(f"sacctmgr remove error: {output}")

    # try:
    #     if "Nothing new added" not in output:
    #         run(["sacctmgr", "create", "user", user, f"defaultaccount={env.SLURMUSER}", "adminlevel=[None]", "--immediate"])
    # except Exception as e:
    #     raise Exception("Problem on sacctmgr create user") from e


def remove_user(user):
    cmd = ["sacctmgr", "remove", "user", "where", f"user={user}", "--immediate"]
    p, output, error_msg = popen_communicate(cmd)
    if p.returncode and "Nothing deleted" not in output:
        log(f"E: sacctmgr remove error: {output}")
        raise BashCommandsException(p.returncode, output, error_msg, str(cmd))


def get_idle_cores(is_print=True) -> int:
    """Return idle cores.

    __ https://stackoverflow.com/a/50095154/2402577
    """
    core_info = run(["sinfo", "-h", "-o%C"]).split("/")
    if len(core_info):
        allocated_cores = core_info[0]
        idle_cores = core_info[1]
        other_cores = core_info[2]
        total_cores = core_info[3]
        if is_print:
            log(
                f"==> [green]allocated_cores=[/green]{allocated_cores} | "
                f"[green]idle_cores=[/green]{idle_cores} | "
                f"[green]other_cores=[/green]{other_cores} | "
                f"[green]total_cores=[/green]{total_cores}"
            )
    else:
        log("E: sinfo return emptry string")
        return 0

    return idle_cores


def pending_jobs_check():
    """If there is no idle cores, waits for idle cores to be emerged."""
    idle_cores = get_idle_cores()
    print_flag = False
    while idle_cores is None:
        if not print_flag:
            log("waiting running jobs to be completed...")
            print_flag = True

        idle_cores = get_idle_cores(is_print=False)
        time.sleep(10)


def is_on() -> bool:
    """Check whether Slurm runs on the background or not, if not runs slurm."""
    log("## checking slurm[yellow]... ", end="")
    processes = ["\<slurmd\>", "\<slurmdbd\>", "\<slurmctld\>"]
    for process_name in processes:
        if not is_process_on(process_name, process_name, process_count=0, is_print=False):
            log("[  [red]failed[/red]  ]", "bold")
            process_name = process_name.replace("\\", "").replace(">", "").replace("<", "")
            raise QuietExit(
                f"E: [bold green]{process_name}[/bold green] is not running in the background. Please run:\n"
                f"[yellow]sudo {env.BASH_SCRIPTS_PATH}/run_slurm.sh"
            )

    # , "\<sacctmgr\>"
    output = run(["sinfo", "-N", "-l"])
    if "PARTITION" not in output:
        log("E: sinfo returns invalid string. Please run:\nsudo ./bash_scripts/run_slurm.sh\n")
        if not output:
            log(f"E: {output}")
        try:
            log("Starting Slurm... \n")
            run(["sudo", env.BASH_SCRIPTS_PATH / "run_slurm.sh"])
            return True
        except:
            return False
    elif "sinfo: error" in output:
        log(f"Error on munged: \n {output}\nrun:\nsudo munged -f \n/etc/init.d/munge start")
        return False
    else:
        log(ok())
        return True


def get_elapsed_time(slurm_job_id) -> int:
    try:
        cmd = ["sacct", "-n", "-X", "-j", slurm_job_id, "--format=Elapsed"]
        elapsed_time = run(cmd)
    except Exception as e:
        raise QuietExit from e

    log(f"elapsed_time={elapsed_time}", "bold")
    elapsed_time = elapsed_time.split(":")
    elapsed_day = "0"
    elapsed_hour = elapsed_time[0].strip()
    elapsed_minute = elapsed_time[1].rstrip()
    if "-" in str(elapsed_hour):
        elapsed_hour = elapsed_hour.split("-")
        elapsed_day = elapsed_hour[0]
        elapsed_hour = elapsed_hour[1]

    elapsed_time = int(elapsed_day) * 1440 + int(elapsed_hour) * 60 + int(elapsed_minute) + 1
    log(f"elapsed_time={elapsed_time}", "bold")
    return elapsed_time


def get_job_end_time(slurm_job_id) -> int:
    """Get the end time of the job in universal time"""
    end_time = run(["sacct", "-n", "-X", "-j", slurm_job_id, "--format=End"])
    if end_time == "":
        log(f"E: slurm_load_jobs error: Invalid job_id ({slurm_job_id}) specified.")
        raise QuietExit

    try:  # cmd: date -d 2018-09-09T21:50:51 +"%s"
        end_time_stamp = run(["date", "-d", end_time, "+'%s'"])
    except Exception as e:
        raise QuietExit from e

    end_time_stamp = end_time_stamp.rstrip().replace("'", "")
    log(f"==> end_time_stamp={end_time_stamp}")
    return end_time_stamp
