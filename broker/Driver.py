#!/usr/bin/env python3

import os
import sys
import textwrap
import time
from datetime import datetime
from functools import partial
from pprint import pprint

import zc.lockfile
from ipdb import launch_ipdb_on_exception

import broker.config as config
import broker.eblocbroker.Contract as Contract
import broker.libs.eudat as eudat
import broker.libs.gdrive as gdrive
import broker.libs.slurm as slurm
from broker._utils.tools import _colorize_traceback, log
from broker.config import env, logging, setup_logger
from broker.drivers.eudat import EudatClass
from broker.drivers.gdrive import GdriveClass
from broker.drivers.ipfs import IpfsClass
from broker.eblocbroker.job import DataStorage
from broker.helper import helper
from broker.lib import eblocbroker_function_call, run_storage_thread, session_start_msg, state
from broker.libs.user_setup import give_RWE_access, user_add
from broker.utils import (
    CacheType,
    StorageID,
    _run_ipfs_daemon,
    bytes32_to_ipfs,
    check_ubuntu_packages,
    eth_address_to_md5,
    get_time,
    is_driver_on,
    is_geth_on,
    is_internet_on,
    is_program_valid,
    question_yes_no,
    read_file,
    run,
    sleep_timer,
    terminate,
    write_to_file,
)

# from threading import Thread
# from multiprocessing import Process
args = helper()
given_block_number = vars(args)["bn"]
pid = str(os.getpid())


def wait_until_idle_core_available():
    """Wait until an idle core become available."""
    while True:
        idle_cores = slurm.get_idle_cores(is_print_flag=False)
        # log(f"idle_cores={idle_cores}", "blue")
        if idle_cores == 0:
            sleep_timer(sleep_duration=60)
        else:
            break


def tools(block_number):
    """Check whether the required functions are in use or not."""
    session_start_msg(env.SLURMUSER, block_number, pid)
    if not is_internet_on():
        terminate("E: Network connection is down. Please try again")
    try:
        if not env.IS_BLOXBERG:
            is_geth_on()
        else:
            log("Connected into BLOXBERG", "green")
        slurm.is_on()
    except Exception as e:
        if type(e).__name__ != "QuietExit":
            _colorize_traceback(e)
        sys.exit(1)

    # run_driver_cancel()  # TODO: uncomment
    if env.IS_EUDAT_USE:
        if not env.OC_USER:
            terminate(f"E: OC_USER is not set in {env.LOG_PATH}/.env")
        else:
            eudat.login(env.OC_USER, f"{env.LOG_PATH}/.eudat_provider.txt", env.OC_CLIENT)

    if env.IS_GDRIVE_USE:
        is_program_valid(["gdrive", "version"])
        try:
            provider_info = config.Ebb.get_provider_info(env.PROVIDER_ID)
        except Exception as e:
            terminate(e)

        _email = provider_info["email"]
        output, gdrive_email = gdrive.check_user(_email)
        if not output:
            terminate(
                f"E: Provider's email address ({_email}) does not match\n"
                f"with the set gdrive address ({gdrive_email})"
            )
        else:
            log(f"==> provider_email={_email}")

    if env.IS_IPFS_USE:
        _run_ipfs_daemon()

    if not check_ubuntu_packages():
        sys.exit(1)


class Driver:
    """Driver Class."""

    def __init__(self):
        """Create new Driver object."""
        self.Ebb = Contract.eblocbroker
        self.logged_jobs_to_process = None
        #: Indicates Lock check for the received job whether received or not
        self.is_provider_received_job = False

    def is_job_received(self, key, index) -> None:
        """Preventing to download or submit again."""
        if config.Ebb.mongo_broker.is_received(str(self.requester_id), key, index):
            raise Exception("## [ mongoDB ] Job is already received", "green")

        if self.job_infos[0]["stateCode"] == state.code["COMPLETED"]:
            raise Exception("Job is already completed.")

        if self.job_infos[0]["stateCode"] == state.code["REFUNDED"]:
            raise Exception("Job is refunded.")

        if not self.job_infos[0]["stateCode"] == state.code["SUBMITTED"]:
            raise Exception("Warning: Job is already captured and in process or completed.")

    def check_requested_job(self, job_key, index) -> None:
        """Check status of the job."""
        if not self.job_infos[0]["core"] or not self.job_infos[0]["run_time"]:
            raise Exception("E: Requested job does not exist")

        if not config.Ebb.does_requester_exist(self.requester_id):
            raise Exception("E: job owner is not registered")

        self.is_job_received(job_key, index)

    def analyze_data(self, key, requester):
        """Obtain information related to source-code data."""
        for idx, source_code_hash_byte in enumerate(self.logged_job.args["sourceCodeHash"]):
            if idx > 0:
                log("")

            if self.cloud_storage_id[idx] in (StorageID.IPFS, StorageID.IPFS_GPG):
                source_code_hash = bytes32_to_ipfs(source_code_hash_byte)
                if idx == 0 and key != source_code_hash:
                    log("E: IPFS hash does not match with the given source_code_hash")
                    continue
            else:
                source_code_hash = config.w3.toText(source_code_hash_byte)

            ##############
            received_storage_deposit = self.Ebb.get_received_storage_deposit(
                env.PROVIDER_ID, requester, source_code_hash
            )
            job_storage_time = self.Ebb.get_job_storage_time(env.PROVIDER_ID, source_code_hash, _from=env.PROVIDER_ID)
            ############
            ds = DataStorage(job_storage_time)
            ds.received_storage_deposit = received_storage_deposit
            self.received_block.append(ds.received_block)
            self.storage_duration.append(ds.storage_duration)
            self.is_already_cached[source_code_hash] = False  # FIXME double check
            # if remaining time to cache is 0, then caching is requested for the related source_code_hash
            if ds.received_block + ds.storage_duration >= self.block_number:
                if ds.received_block < self.block_number:
                    self.is_already_cached[source_code_hash] = True
                elif ds.received_block == self.block_number:
                    if source_code_hash in self.is_already_cached:
                        self.is_already_cached[source_code_hash] = True
                    else:
                        # for the first job should be False since it is
                        # requested for cache for the first time
                        self.is_already_cached[source_code_hash] = False

            log(
                f"source_code_hash[{idx}]={source_code_hash}\n"
                f"received_block={ds.received_block}\n"
                f"storage_duration(block_number)={ds.storage_duration}\n"
                f"cloud_storage_id[{idx}]={StorageID(self.cloud_storage_id[idx]).name}\n"
                f"cached_type={CacheType(self.logged_job.args['cacheType'][idx]).name}\n"
                f"is_already_cached={self.is_already_cached[source_code_hash]}"
            )

    def process_logged_job(self, idx):
        """Process logged job one by one."""
        wait_until_idle_core_available()
        self.is_provider_received_job = True
        columns_size = int(int(columns) / 2 - 12)
        log("-" * columns_size + f" {idx} " + "-" * columns_size, "blue")
        # sourceCodeHash = binascii.hexlify(logged_job.args['sourceCodeHash'][0]).decode("utf-8")[0:32]
        job_key = self.logged_job.args["jobKey"]
        index = self.logged_job.args["index"]
        self.cloud_storage_id = self.logged_job.args["cloudStorageID"]
        self.block_number = self.logged_job["blockNumber"]
        log(f"job_key={job_key} | index={index}", "green")
        log(
            f"received_block_number={self.block_number} \n"
            f"transactionHash={self.logged_job['transactionHash'].hex()} | "
            f"log_index={self.logged_job['logIndex']} \n"
            f"provider={self.logged_job.args['provider']} \n"
            f"received={self.logged_job.args['received']}",
            "yellow",
        )
        self.received_block = []
        self.storage_duration = []
        if self.logged_job["blockNumber"] > self.max_blocknumber:
            self.max_blocknumber = self.logged_job["blockNumber"]

        try:
            run(["bash", f"{env.EBLOCPATH}/broker/bash_scripts/is_str_valid.sh", job_key])
        except Exception:
            logging.error("E: Filename contains an invalid character")
            return

        try:
            job_id = 0  # main job
            self.job_info = eblocbroker_function_call(
                partial(config.Ebb.get_job_info, env.PROVIDER_ID, job_key, index, job_id, self.block_number), attempt=10
            )
            self.job_infos.append(self.job_info)
            self.job_info.update({"received_block": self.received_block})
            self.job_info.update({"storageDuration": self.storage_duration})
            self.job_info.update({"cacheType": self.logged_job.args["cacheType"]})
            self.requester_id = self.job_info["job_owner"]
            log(f"requester={self.requester_id}", "yellow")
            pprint(self.job_info)
        except Exception as e:
            _colorize_traceback(e)
            return

        self.analyze_data(job_key, self.job_info["job_owner"])
        for job in range(1, len(self.job_info["core"])):
            try:
                self.job_infos.append(  # if workflow is given then add jobs into list
                    config.Ebb.get_job_info(env.PROVIDER_ID, job_key, index, job, self.block_number)
                )
            except Exception:
                pass

        self.check_requested_job(job_key, index)

    def sent_job_to_storage_class(self):
        """Submit job's information into related thread."""
        user_add(self.requester_id, env.PROGRAM_PATH, env.SLURMUSER)
        requester_md5_id = eth_address_to_md5(self.requester_id)
        slurm.pending_jobs_check()
        main_cloud_storage_id = self.logged_job.args["cloudStorageID"][0]
        kwargs = {
            "logged_job": self.logged_job,
            "job_info": self.job_infos,
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
                    _colorize_traceback(e)
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
        self.max_blocknumber = 0
        self.is_provider_received_job = False
        self.is_already_cached = {}
        for idx, logged_job in enumerate(self.logged_jobs_to_process):
            self.job_infos = []
            self.logged_job = logged_job
            self.requester_id = None
            try:
                self.process_logged_job(idx)
                self.sent_job_to_storage_class()
            except Exception as e:
                raise e


def run_driver():
    """Run the main driver script for eblocbroker on the background."""
    # dummy sudo command to get the password when session starts for only to
    # create users and submit the slurm job under another user
    run(["sudo", "printf", "hello"])
    env.IS_THREADING_ENABLED = False
    config.logging = setup_logger(env.DRIVER_LOG)
    columns = 100

    # driver_cancel_process = None
    try:
        from imports import connect

        connect()
        Contract.eblocbroker = Contract.Contract()
        driver = Driver()
        Ebb: "Contract.Contract" = Contract.eblocbroker
        driver.Ebb: "Contract.Contract" = Contract.eblocbroker
        config.Ebb = Contract.eblocbroker
        Contract.eblocbroker.ebb = config.ebb  # set for global use across files
        driver.Ebb = Contract.eblocbroker
        driver.Ebb
    except Exception:
        _colorize_traceback()
        terminate()

    if not env.PROVIDER_ID:
        terminate(f"E: PROVIDER_ID is None in {env.LOG_PATH}/.env")

    if not env.WHOAMI or not env.EBLOCPATH or not env.PROVIDER_ID:
        terminate(f"Please run: {env.EBLOCPATH}/broker/bash_scripts/folder_setup.sh")

    if not env.SLURMUSER:
        terminate(f"E: SLURMUSER is not set in {env.LOG_PATH}/.env")

    try:
        deployed_block_number = Ebb.get_deployed_block_number()
    except Exception as e:
        raise e

    if not os.path.isfile(env.BLOCK_READ_FROM_FILE):
        write_to_file(env.BLOCK_READ_FROM_FILE, deployed_block_number)

    if given_block_number > 0:
        block_number_saved = int(given_block_number)
    else:
        block_number_saved = read_file(env.BLOCK_READ_FROM_FILE)
        if not block_number_saved.isdigit():
            log("E: BLOCK_READ_FROM_FILE is empty or contains an invalid character")
            question_yes_no(
                "## Would you like to read from the contract's deployed block number? [Y/n]: ", is_terminate=True
            )
            block_number_saved = deployed_block_number
            if deployed_block_number:
                write_to_file(env.BLOCK_READ_FROM_FILE, deployed_block_number)
            else:
                log(f"E: deployed_block_number={deployed_block_number} is invalid")
                terminate()

    tools(block_number_saved)
    try:
        Ebb.is_contract_exists()
    except Exception:
        terminate(
            "E: Contract address does not exist on the blockchain, is the blockchain sync?\n"
            f"block_number={Ebb.get_block_number()}",
            is_traceback=False,
        )

    if env.IS_THREADING_ENABLED:
        log(f"is_threading={env.IS_THREADING_ENABLED}", "blue")

    Ebb.is_eth_account_locked(env.PROVIDER_ID)
    log(f"==> is_web3_connected={Ebb.is_web3_connected()}")
    log(f"==> whoami={env.WHOAMI}")
    log(f"==> log_file={env.DRIVER_LOG}")
    log(f"==> rootdir={os.getcwd()}")
    if not Ebb.does_provider_exist(env.PROVIDER_ID):
        # Updated since cluster is not registered
        write_to_file(env.BLOCK_READ_FROM_FILE, Ebb.get_block_number())
        terminate(
            textwrap.fill(
                f"E: Your Ethereum address {env.PROVIDER_ID} "
                "does not match with any provider in eBlocBroker. Please register your "
                "provider using your Ethereum Address in to the eBlocBroker. You can "
                "use eblocbroker/register_provider.py script to register your provider."
            ),
            is_traceback=False,
        )

    if not Ebb.is_orcid_verified(env.PROVIDER_ID):
        terminate(f"E: Provider's ({env.PROVIDER_ID}) ORCID is not verified")

    block_read_from = block_number_saved
    balance_temp = Ebb.get_balance(env.PROVIDER_ID)
    log(f"==> deployed_block_number={deployed_block_number}")
    log(f"==> balance={balance_temp}")
    while True:
        wait_until_idle_core_available()
        time.sleep(0.2)
        if not str(block_read_from).isdigit():
            terminate(f"E: block_read_from={block_read_from}")

        balance = Ebb.get_balance(env.PROVIDER_ID)
        try:
            squeue_output = run(["squeue"])
            if "squeue: error:" in str(squeue_output):
                raise
        except:
            terminate("E: SLURM is not running on the background. Please run:\nsudo ./broker/bash_scripts/run_slurm.sh")

        # Gets real info under the header after the first line
        if len(f"{squeue_output}\n".split("\n", 1)[1]) > 0:
            # checks if the squeue output's line number is gretaer than 1
            log(f"Current slurm running jobs status:\n{squeue_output}", "yellow")
            log("-" * int(columns), "green")

        log(f"==> date=[{get_time()}]")
        if isinstance(balance, int):
            log(f"==> provider_gained_wei={int(balance) - int(balance_temp)}")

        current_block_number = Ebb.get_block_number()
        log(f"==> waiting new job to come since block number={block_read_from}")
        log(f"==> current_block={current_block_number} | sync_from={block_read_from}")
        # log(f"block_read_from={block_read_from}")
        flag = True
        while current_block_number < int(block_read_from):
            current_block_number = Ebb.get_block_number()
            if flag:
                log(
                    f"## Waiting block number to be updated, it remains constant at {current_block_number}...",
                    "blue",
                )
            flag = False
            time.sleep(0.25)

        log(f"Passed incremented block number... Watching from block number={block_read_from}", "yellow")
        block_read_from = str(block_read_from)  # reading event's location has been updated
        slurm.pending_jobs_check()
        driver.logged_jobs_to_process = Ebb.run_log_job(block_read_from, env.PROVIDER_ID)
        try:
            driver.process_logged_jobs()
        except Exception as e:
            _colorize_traceback(e)
            breakpoint()  # DEBUG
            sys.exit(1)

        if len(driver.logged_jobs_to_process) > 0 and driver.max_blocknumber > 0:
            # updates the latest read block number
            block_read_from = driver.max_blocknumber + 1
            write_to_file(env.BLOCK_READ_FROM_FILE, block_read_from)
        if not driver.is_provider_received_job:
            # If there is no submitted job for the provider, than block start
            # to read from the current block number and updates the latest read
            # block number read from the file
            write_to_file(env.BLOCK_READ_FROM_FILE, current_block_number)
            block_read_from = current_block_number


if __name__ == "__main__":
    try:
        columns = 104
        _columns = int(int(columns) / 2 - 12)
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
        log(date_now + " " + "=" * (_columns - 16) + " provider session starts " + "=" * (_columns - 5), "cyan")
        with launch_ipdb_on_exception():
            # if an exception is raised, enclose code with the `with` statement
            # to launch ipdb
            lock = None
            try:
                is_driver_on(process_count=1)
                try:
                    lock = zc.lockfile.LockFile(env.DRIVER_LOCKFILE, content_template=pid)
                except PermissionError:
                    log("E: PermissionError is generated for the locked file")
                    _colorize_traceback()
                    give_RWE_access(env.WHOAMI, "/tmp/run")
                    lock = zc.lockfile.LockFile(env.DRIVER_LOCKFILE, content_template=pid)
                # open(env.DRIVER_LOCKFILE, 'w').close()
                run_driver()
            except zc.lockfile.LockError:
                log("E: Driver cannot lock the file, the pid file is in use", "red")
            # except config.QuietExit:
            #     pass
            except Exception as e:
                _colorize_traceback(e)
            finally:
                try:
                    if lock:
                        lock.close()
                        open(env.DRIVER_LOCKFILE, "w").close()
                except Exception as e:
                    _colorize_traceback(e)
    except Exception as e:
        if type(e).__name__ != "KeyboardInterrupt":
            _colorize_traceback(e)
        sys.exit(1)
