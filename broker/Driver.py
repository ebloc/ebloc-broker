#!/usr/bin/env python3

"""Driver for ebloc-broker."""

import os
import sys
import textwrap
import time
from contextlib import suppress
from datetime import datetime
from functools import partial

import zc.lockfile
from ipdb import launch_ipdb_on_exception

from broker import cfg, config
from broker._utils import _log
from broker._utils._log import _console_ruler, log
from broker._utils.tools import kill_process_by_name, print_tb
from broker.config import Terminate, env, logging, setup_logger
from broker.drivers.eudat import EudatClass
from broker.drivers.gdrive import GdriveClass
from broker.drivers.ipfs import IpfsClass
from broker.eblocbroker import Contract
from broker.errors import HandlerException, JobException, QuietExit
from broker.helper import helper
from broker.lib import eblocbroker_function_call, run_storage_thread, session_start_msg, state
from broker.libs import eudat, gdrive, slurm
from broker.libs.user_setup import give_rwe_access, user_add
from broker.utils import (
    StorageID,
    check_ubuntu_packages,
    eth_address_to_md5,
    get_time,
    is_driver_on,
    is_geth_on,
    is_internet_on,
    is_program_valid,
    question_yes_no,
    run,
    run_ipfs_daemon,
    sleep_timer,
    terminate,
)

# from threading import Thread
# from multiprocessing import Process
args = helper()

if vars(args)["latest"]:
    given_block_number = cfg.Ebb.get_block_number()
else:
    given_block_number = vars(args)["bn"]

pid = str(os.getpid())


def wait_until_idle_core_available():
    """Wait until an idle core become available."""
    while True:
        idle_cores = slurm.get_idle_cores(is_print=False)
        # log(f"idle_cores={idle_cores}", "blue")
        if idle_cores == 0:
            sleep_timer(sleep_duration=60)
        else:
            break


def _tools(block_continue):
    """Check whether the required functions are in use or not."""
    session_start_msg(env.SLURMUSER, block_continue, pid)
    try:
        if not is_internet_on():
            raise Terminate("Network connection is down. Please try again")

        if not check_ubuntu_packages():
            raise Terminate()

        if not env.IS_BLOXBERG:
            is_geth_on()
        else:
            log(":beer: Connected into [green]BLOXBERG[/green]", "bold")

        slurm.is_on()
        # run_driver_cancel()  # TODO: uncomment
        if env.IS_EUDAT_USE:
            if not env.OC_USER:
                raise Terminate(f"OC_USER is not set in {env.LOG_PATH.joinpath('.env')}")

            eudat.login(env.OC_USER, env.LOG_PATH.joinpath(".eudat_provider.txt"), env.OC_CLIENT)

        if env.IS_GDRIVE_USE:
            is_program_valid(["gdrive", "version"])
            if env.GDRIVE == "":
                raise Terminate(f"E: Path for gdrive='{env.GDRIVE}' please set a valid path in the .env file")

            provider_info = Contract.Ebb.get_provider_info(env.PROVIDER_ID)
            email = provider_info["email"]
            output, gdrive_email = gdrive.check_user(email)
            if not output:
                msg = f"Provider's email address ({email}) does not match with the set gdrive's ({gdrive_email})"
                raise Terminate(msg)

            log(f"==> provider_email=[magenta]{email}")

        if env.IS_IPFS_USE:
            if not os.path.isfile(env.GPG_PASS_FILE):
                log(f"E: Please store your gpg password in the {env.GPG_PASS_FILE}\nfile for decrypting using ipfs")
                raise QuietExit

            run_ipfs_daemon()
    except QuietExit as e:
        raise e
    except Exception as e:
        print_tb(e)
        raise Terminate from e


class Driver:
    """Driver Class."""

    def __init__(self):
        """Create new Driver object."""
        self.Ebb: "Contract.Contract" = cfg.Ebb
        self.block_number: int = 0
        self.latest_block_number: int = 0
        self.logged_jobs_to_process = None
        self.job_info = None
        self.job_infos = {}
        self.requester_id: str = ""
        #: Indicates Lock check for the received job whether received or not
        self.is_provider_received_job = False

    def is_job_received(self, key, index) -> None:
        """Preventing to download or submit again."""
        if self.Ebb.mongo_broker.is_received(str(self.requester_id), key, index):
            raise JobException("## [ mongo_db ] Job is already received")

        if self.job_infos[0]["stateCode"] == state.code["COMPLETED"]:
            raise JobException("## Job is already completed.")

        if self.job_infos[0]["stateCode"] == state.code["REFUNDED"]:
            raise JobException("## Job is refunded.")

        if not self.job_infos[0]["stateCode"] == state.code["SUBMITTED"]:
            raise JobException("warning: Job is already captured and in process or completed.")

    def check_requested_job(self, key, index) -> None:
        """Check status of the job."""
        if not self.job_infos[0]["core"] or not self.job_infos[0]["run_time"]:
            raise JobException("E: Requested job does not exist")

        if not self.Ebb.does_requester_exist(self.requester_id):
            raise JobException("E: job owner is not registered")

        self.is_job_received(key, index)

    def process_logged_job(self, idx):
        """Process logged job one by one."""
        self.received_block = []
        self.storage_duration = []
        wait_until_idle_core_available()
        self.is_provider_received_job = True
        _console_ruler(idx, character="-")
        # sourceCodeHash = binascii.hexlify(logged_job.args['sourceCodeHash'][0]).decode("utf-8")[0:32]
        job_key = self.logged_job.args["jobKey"]
        index = self.logged_job.args["index"]
        self.job_block_number = self.logged_job["blockNumber"]
        self.cloud_storage_id = self.logged_job.args["cloudStorageID"]
        log(f"job_key={job_key} | index={index}", "bold green")
        log(
            f"received_block_number={self.job_block_number} \n"
            f"transactionHash={self.logged_job['transactionHash'].hex()} | "
            f"log_index={self.logged_job['logIndex']} \n"
            f"provider={self.logged_job.args['provider']} \n"
            f"received={self.logged_job.args['received']}",
            "bold yellow",
        )
        if self.logged_job["blockNumber"] > self.latest_block_number:
            self.latest_block_number = self.logged_job["blockNumber"]

        try:
            run([env.BASH_SCRIPTS_PATH / "is_str_valid.sh", job_key])
        except:
            logging.error("E: Filename contains an invalid character")
            return

        try:
            job_id = 0  # main job_id
            self.job_info = eblocbroker_function_call(
                partial(self.Ebb.get_job_info, env.PROVIDER_ID, job_key, index, job_id, self.job_block_number),
                max_retries=10,
            )
            cfg.Ebb.get_job_source_code_hashes(env.PROVIDER_ID, job_key, index, self.job_block_number)
            self.requester_id = self.job_info["job_owner"]
            self.job_info.update({"received_block": self.received_block})
            self.job_info.update({"storage_duration": self.storage_duration})
            self.job_info.update({"cacheType": self.logged_job.args["cacheType"]})
            cfg.Ebb.analyze_data(job_key, env.PROVIDER_ID)
            self.job_infos.append(self.job_info)
            log(f"requester={self.requester_id}", "bold yellow")
            log(self.job_info)
        except Exception as e:
            print_tb(e)
            return

        for job in range(1, len(self.job_info["core"])):
            with suppress(Exception):
                self.job_infos.append(  # if workflow is given then add jobs into list
                    self.Ebb.get_job_info(env.PROVIDER_ID, job_key, index, job, self.job_block_number)
                )

        self.check_requested_job(job_key, index)

    def sent_job_to_storage_class(self):
        """Submit job's information into related thread."""
        user_add(self.requester_id, env.PROGRAM_PATH, env.SLURMUSER)
        requester_md5_id = eth_address_to_md5(self.requester_id)
        slurm.pending_jobs_check()
        main_cloud_storage_id = self.logged_job.args["cloudStorageID"][0]
        kwargs = {
            "logged_job": self.logged_job,
            "job_infos": self.job_infos,
            "requester_id": requester_md5_id,
            "is_already_cached": self.is_already_cached,
        }
        if main_cloud_storage_id in (StorageID.IPFS, StorageID.IPFS_GPG):
            storage_class = IpfsClass(**kwargs)
        elif main_cloud_storage_id == StorageID.EUDAT:
            if not config.oc:
                try:
                    eudat.login(env.OC_USER, f"{env.LOG_PATH}/.eudat_provider.txt", env.OC_CLIENT)
                except Exception as e:
                    print_tb(e)
                    sys.exit(1)

            storage_class = EudatClass(**kwargs)
            # thread.start_new_thread(driverFunc.driver_eudat, (logged_job, jobInfo, requester_md5_id))
        elif main_cloud_storage_id == StorageID.GDRIVE:
            storage_class = GdriveClass(**kwargs)

        # run_storage_process(storage_class)
        if env.IS_THREADING_ENABLED:
            run_storage_thread(storage_class)
        else:
            storage_class.run()

    def process_logged_jobs(self):
        """Process logged jobs."""
        self.latest_block_number = 0
        self.is_provider_received_job = False
        self.is_already_cached = {}
        for idx, logged_job in enumerate(self.logged_jobs_to_process):
            self.job_infos = []
            self.logged_job = logged_job
            self.requester_id = None
            try:
                self.process_logged_job(idx)
                self.sent_job_to_storage_class()
            except JobException as e:
                log(str(e))
            except Exception as e:
                raise e


def run_driver():
    """Run the main driver script for eblocbroker on the background."""
    # dummy sudo command to get the password when session starts for only to
    # create users and submit the slurm job under another user
    run(["sudo", "printf", "hello"])
    kill_process_by_name("gpg-agent")
    env.IS_THREADING_ENABLED = False
    config.logging = setup_logger(_log.DRIVER_LOG)
    # driver_cancel_process = None
    try:
        from broker.imports import connect

        connect()
        Ebb: "Contract.Contract" = cfg.Ebb
        driver = Driver()
    except Exception as e:
        raise Terminate from e

    if not env.PROVIDER_ID:
        raise Terminate(f"PROVIDER_ID is None in {env.LOG_PATH}/.env")

    if not env.WHOAMI or not env.EBLOCPATH or not env.PROVIDER_ID:
        raise Terminate(f"Please run: {env.BASH_SCRIPTS_PATH}/folder_setup.sh")

    if not env.SLURMUSER:
        raise Terminate(f"SLURMUSER is not set in {env.LOG_PATH}/.env")

    try:
        deployed_block_number = Ebb.get_deployed_block_number()
    except Exception as e:
        raise e

    if not env.config["block_continue"]:
        env.config["block_continue"] = deployed_block_number

    if given_block_number > 0:
        block_number_saved = int(given_block_number)
    else:
        block_number_saved = env.config["block_continue"]
        if not isinstance(env.config["block_continue"], int):
            log("E: block_continue variable is empty or contains an invalid character")
            question_yes_no("#> Would you like to read from the contract's deployed block number?", is_terminate=True)
            block_number_saved = deployed_block_number
            if deployed_block_number:
                env.config["block_continue"] = deployed_block_number
            else:
                raise Terminate(f"deployed_block_number={deployed_block_number} is invalid")

    _tools(block_number_saved)
    try:
        Ebb.is_contract_exists()
    except:
        terminate(
            "Contract address does not exist on the blockchain, is the blockchain sync?\n"
            f"block_number={Ebb.get_block_number()}",
            is_traceback=False,
        )

    if env.IS_THREADING_ENABLED:
        log(f"## is_threading={env.IS_THREADING_ENABLED}")

    Ebb.is_eth_account_locked(env.PROVIDER_ID)
    log(f"==> whoami={env.WHOAMI}")
    log(f"==> is_web3_connected={Ebb.is_web3_connected()}")
    log(f"==> log_file={_log.DRIVER_LOG}")
    log(f"==> rootdir={os.getcwd()}")
    if not Ebb.does_provider_exist(env.PROVIDER_ID):
        # updated since cluster is not registered
        env.config["block_continue"] = Ebb.get_block_number()
        terminate(
            textwrap.fill(
                f"Your Ethereum address {env.PROVIDER_ID} "
                "does not match with any provider in eBlocBroker. Please register your "
                "provider using your Ethereum Address in to the eBlocBroker. You can "
                "use eblocbroker/register_provider.py script to register your provider."
            ),
            is_traceback=False,
        )

    if not Ebb.is_orcid_verified(env.PROVIDER_ID):
        raise Terminate(f"Provider's ({env.PROVIDER_ID}) ORCID is not verified")

    block_read_from = block_number_saved
    balance_temp = Ebb.get_balance(env.PROVIDER_ID)
    eth_balance = Ebb.eth_balance(env.PROVIDER_ID)
    log(f"==> deployed_block_number={deployed_block_number}")
    log(f"==> account_balance={eth_balance} gwei | {cfg.w3.fromWei(eth_balance, 'ether')} eth")
    log(f"==> Ebb_balance={balance_temp}")
    while True:
        wait_until_idle_core_available()
        time.sleep(0.2)
        if not str(block_read_from).isdigit():
            raise Terminate(f"block_read_from={block_read_from}")

        balance = Ebb.get_balance(env.PROVIDER_ID)
        try:
            squeue_output = run(["squeue"])
            if "squeue: error:" in str(squeue_output):
                raise
        except Exception as e:
            raise Terminate(
                "Warning: SLURM is not running on the background. Please run:\n"
                "sudo ./broker/bash_scripts/run_slurm.sh"
            ) from e

        # Gets real info under the header after the first line
        if len(f"{squeue_output}\n".split("\n", 1)[1]) > 0:
            # checks if the squeue output's line number is gretaer than 1
            log(f"Current slurm running jobs status:\n{squeue_output}", "bold yellow")
            _console_ruler()

        log(f"==> date={get_time()}")
        if isinstance(balance, int):
            value = int(balance) - int(balance_temp)
            if value > 0:
                log(f"==> Since Driver started provider_gained_wei={value}")

        current_block_num = Ebb.get_block_number()
        log(f"==> waiting new job to come since block_number={block_read_from}")
        log(f"==> current_block={current_block_num} | sync_from={block_read_from}")
        # log(f"block_read_from={block_read_from}")
        flag = True
        while current_block_num < int(block_read_from):
            current_block_num = Ebb.get_block_number()
            if flag:
                log(
                    f"## Waiting block number to be updated. It remains constant at {current_block_num}...", "bold blue"
                )

            flag = False
            time.sleep(0.25)

        log(f"#> [bold yellow]Passed incremented block number... Watching from block_number=[cyan]{block_read_from}")
        block_read_from = str(block_read_from)  # reading event's location has been updated
        slurm.pending_jobs_check()
        driver.logged_jobs_to_process = Ebb.run_log_job(block_read_from, env.PROVIDER_ID)
        driver.process_logged_jobs()
        if len(driver.logged_jobs_to_process) > 0 and driver.latest_block_number > 0:
            # updates the latest read block number
            block_read_from = driver.latest_block_number + 1
            env.config["block_continue"] = block_read_from
        if not driver.is_provider_received_job:
            # If there is no submitted job for the provider, than block start
            # to read from the current block number and updates the latest read
            # block number read from the file
            env.config["block_continue"] = current_block_num
            block_read_from = current_block_num


def _main():
    lock = None
    try:
        is_driver_on(process_count=1, is_print=False)
        try:
            lock = zc.lockfile.LockFile(env.DRIVER_LOCKFILE, content_template=pid)
        except PermissionError:
            print_tb("E: PermissionError is generated for the locked file")
            give_rwe_access(env.WHOAMI, "/tmp/run")
            lock = zc.lockfile.LockFile(env.DRIVER_LOCKFILE, content_template=pid)

        run_driver()
    except HandlerException:
        pass
    except QuietExit:
        pass
    except zc.lockfile.LockError:
        log("E: Driver cannot lock the file, the pid file is in use")
    except Terminate as e:
        terminate(str(e), lock)
    except Exception as e:
        print_tb(e)
    finally:
        with suppress(Exception):
            if lock:
                lock.close()

        breakpoint()  # DEBUG: end of program


def main():
    try:
        _console_ruler("provider session starts")
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
        log(f"==> date={date_now}")
        with launch_ipdb_on_exception():
            # if an exception is raised, enclose code with the `with` statement to launch ipdb
            _main()
    except KeyboardInterrupt:
        sys.exit(1)
