#!/usr/bin/env python3

import re
import time
from contextlib import suppress
from broker._utils._log import log, ok
from broker._utils.tools import is_process_on
from broker.config import env
from broker.errors import BashCommandsException, QuietExit, Terminate
from broker.lib import run
from broker.utils import popen_communicate, is_docker


def add_account_to_slurm(user):
    cmd = ["sacctmgr", "add", "account", user, "--immediate"]
    p, output, *_ = popen_communicate(cmd)
    if p.returncode > 0 and "Nothing new added" not in str(output):
        raise Exception(f"E: {' '.join(cmd)}\nsacctmgr remove error: {output}")


def add_user_to_slurm(user):
    #: remove__user(user)
    add_account_to_slurm(user)
    cmd = ["sacctmgr", "add", "user", user, f"account={user}", "--immediate"]
    # cmd = ["sacctmgr", "add", "account", user, "--immediate"]
    p, output, *_ = popen_communicate(cmd)
    if p.returncode > 0:
        try:
            if "Nothing new added" not in output:  # output could be: b''
                raise Exception(f"E: {' '.join(cmd)}\nsacctmgr remove error: {output}")
        except:
            pass

    # try:
    #     if "Nothing new added" not in output:
    #         run(["sacctmgr", "create", "user", user, f"defaultaccount={env.SLURMUSER}", "adminlevel=[None]", "--immediate"])
    # except Exception as e:
    #     raise Exception("Problem on sacctmgr create user") from e


def remove_user(user) -> None:
    cmd = ["sacctmgr", "remove", "user", "where", f"user={user}", "--immediate"]
    p, output, error_msg = popen_communicate(cmd)
    if p.returncode and "Nothing deleted" not in output:
        log(f"E: sacctmgr remove error: {output}")
        raise BashCommandsException(p.returncode, output, error_msg, str(cmd))


def get_idle_cores(is_print=True) -> int:
    """Return idle cores.

    * slurm: Is there any way to return unused core number?
    __ https://stackoverflow.com/a/50095154/2402577
    __ https://slurm.schedmd.com/sinfo.html
    """
    core_info = run(["sinfo", "-h", "-o%C"]).split("/")
    if len(core_info):
        allocated_cores = int(core_info[0])
        idle_cores = int(core_info[1])
        other_cores = int(core_info[2])
        total_cores = int(core_info[3])
        if is_print:
            log(
                f"==> [g]allocated_cores=[/g]{allocated_cores} | "
                f"[g]idle_cores=[/g]{idle_cores} | "
                f"[g]other_cores=[/g]{other_cores} | "
                f"[g]total_cores=[/g]{total_cores}"
            )
    else:
        log("E: sinfo return emptry string")
        return 0

    return idle_cores


def pending_jobs_check(is_print=True):
    """If there is no idle cores, waits for idle cores to be emerged."""
    idle_cores = get_idle_cores(is_print)
    print_flag = False
    while idle_cores is None:
        if not print_flag:
            log("waiting running jobs to be completed...")
            print_flag = True

        idle_cores = get_idle_cores(is_print=False)
        time.sleep(10)


def is_on() -> bool:
    """Check whether Slurm runs on the background or not, if not runs slurm."""
    log("==> Checking slurm[yellow]... ", end="")
    processes = ["\<slurmd\>", "\<slurmdbd\>", "\<slurmctld\>"]
    for process_name in processes:
        if not is_process_on(process_name, process_name, process_count=0, is_print=False):
            log("[  [red]failed[/red]  ]", "bold")
            process_name = process_name.replace("\\", "").replace(">", "").replace("<", "")
            raise Terminate(
                f"E: '{process_name}' is not running in the background. Please run:\n"
                f"'sudo {env.BASH_SCRIPTS_PATH}/run_slurm.sh'"
            )

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
        if is_docker():
            with suppress(Exception):
                run(["sudo", "groupadd", "eblocbroker"])

            with suppress(Exception):
                run(["sacctmgr", "add", "cluster", "eblocbroker", "--immediate"])

            with suppress(Exception):  # kama ipfs node
                ipfs_id = "/ip4/195.238.122.141/tcp/4001/p2p/12D3KooWM8EsuoC5wTA6wx3Qn42UcBe98y4j9tgQQ9J4WHHvqpUy"
                run(["ipfs", "swarm", "connect", ipfs_id], suppress_stderr=True)

        return True


def scontrol_parse(slurm_job_id, _from, to):
    cmd = ["sacct", "-n", "-X", "-j", slurm_job_id, "--format=Elapsed"]
    elapsed_time = run(cmd)
    if not elapsed_time:
        output = run(["scontrol", "show", f"job={slurm_job_id}"])
        for line in output.split("\n"):
            if _from in line:
                # StartTime=2023-07-01T19:05:54 EndTime=2023-07-01T19:06:44 Deadline=N/A
                result = re.search(f"{_from}(.*){to}", line)
                return result.group(1)  # type: ignore


def get_elapsed_time(slurm_job_id) -> int:
    try:
        cmd = ["sacct", "-n", "-X", "-j", slurm_job_id, "--format=Elapsed"]
        elapsed_time = run(cmd)
        if not elapsed_time:
            elapsed_time = scontrol_parse(slurm_job_id, "RunTime=", " TimeLimit=")
    except Exception as e:
        elapsed_time = scontrol_parse(slurm_job_id, "RunTime=", " TimeLimit=")
        if not elapsed_time:
            raise QuietExit from e

    log(f"==> elapsed_time={elapsed_time} => ", end="")
    elapsed_time = elapsed_time.split(":")
    elapsed_day = "0"
    elapsed_hour = elapsed_time[0].strip()
    elapsed_minute = elapsed_time[1].rstrip()
    if "-" in str(elapsed_hour):
        elapsed_hour = elapsed_hour.split("-")
        elapsed_day = elapsed_hour[0]
        elapsed_hour = elapsed_hour[1]

    elapsed_time = int(elapsed_day) * 1440 + int(elapsed_hour) * 60 + int(elapsed_minute) + 1
    log(f"[cyan]{elapsed_time}[/cyan] minuntes")
    return elapsed_time


def get_job_end_timestamp(slurm_job_id) -> int:
    """Return the end time of the job in universal time."""
    end_timestamp = run(["sacct", "-n", "-X", "-j", slurm_job_id, "--format=End"])
    if end_timestamp == "":
        end_timestamp = scontrol_parse(slurm_job_id, "EndTime=", " Deadline=")
        if not end_timestamp:
            log(f"E: slurm_load_jobs error: Invalid job_id ({slurm_job_id}) specified.")
            raise QuietExit

    try:  # cmd: date -d 2018-09-09T21:50:51 + "%s"
        end_timestamp = run(["date", "-d", end_timestamp, "+'%s'"])
    except Exception as e:
        raise QuietExit from e

    end_timestamp = end_timestamp.rstrip().replace("'", "")
    log(f"==> end_timestamp={end_timestamp}")
    return end_timestamp
