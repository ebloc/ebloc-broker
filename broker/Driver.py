#!/usr/bin/env python3

"""Driver for ebloc-broker."""

import math
import os
import sys
import textwrap
import time
import zc.lockfile
from contextlib import suppress
from datetime import datetime
from decimal import Decimal
from functools import partial
from halo import Halo
from ipdb import launch_ipdb_on_exception
from typing import List

from broker import cfg, config
from broker._import import check_connection
from broker._utils import _log
from broker._utils._log import console_ruler, log
from broker._utils.tools import is_process_on, kill_process_by_name, print_tb, squeue
from broker.config import env, setup_logger
from broker.drivers.b2drop import B2dropClass
from broker.drivers.gdrive import GdriveClass
from broker.drivers.ipfs import IpfsClass
from broker.eblocbroker_scripts.register_provider import get_ipfs_address
from broker.eblocbroker_scripts.utils import Cent
from broker.errors import HandlerException, JobException, QuietExit, Terminate
from broker.imports import nc
from broker.lib import eblocbroker_function_call, pre_check, run_storage_thread, session_start_msg, state
from broker.libs import eudat, gdrive, slurm
from broker.libs.user_setup import give_rwe_access, user_add
from broker.utils import (
    StorageID,
    check_ubuntu_packages,
    eth_address_to_md5,
    get_date,
    is_driver_on,
    is_geth_on,
    is_internet_on,
    is_program_valid,
    question_yes_no,
    run,
    sleep_timer,
    start_ipfs_daemon,
    terminate,
)
from brownie import network

# from urllib3.exceptions import (
#     MaxRetryError,
# )


with suppress(Exception):
    from broker.eblocbroker_scripts import Contract


cfg.IS_BREAKPOINT = True
pid = os.getpid()
Ebb: "Contract.Contract" = cfg.Ebb  # type: ignore

if not cfg.IS_BREAKPOINT:
    os.environ["PYTHONBREAKPOINT"] = "0"


def wait_until_idle_core_is_available():
    """Wait until an idle core becomes available."""
    while True:
        if slurm.get_idle_cores(is_print=False) > 0:
            break
        else:
            log("#> Slurm running node capacity is full.")
            sleep_timer(60)


def tools(bn):
    """Check whether the required functions are running on the background.

    :param bn: Continue from given the block number

    """
    session_start_msg(bn)
    try:
        is_internet_on()
    except Exception as e:
        raise Terminate("Network connection is down. Please try again") from e

    try:
        pre_check()
        if not check_ubuntu_packages():
            raise Terminate

        provider_info_contract = Ebb.get_provider_info(env.PROVIDER_ID)
        if env.IS_BLOXBERG:
            log(":beer:  Connected into [g]bloxberg[/g]")
        else:
            is_geth_on()

        if not Ebb.is_orcid_verified(env.PROVIDER_ID):
            log(f"warning: provider [g]{env.PROVIDER_ID}[/g]'s orcid id is not authenticated yet")
            raise QuietExit

        slurm.is_on()
        if not is_process_on("mongod"):
            raise Exception("mongodb is not running in the background")

        # run_driver_cancel()  # TODO: uncomment
        if env.IS_B2DROP_USE:
            if not env.OC_USER:
                raise Terminate(f"OC_USER is not set in {env.LOG_DIR.joinpath('cfg.yaml')}")

            eudat.login(env.OC_USER, env.LOG_DIR.joinpath(".b2drop_client.txt"), env.OC_CLIENT)

        gmail = provider_info_contract["gmail"]
        log(f"==> [y]provider_gmail[/y]=[m]{gmail}", h=False)
        if env.IS_GDRIVE_USE:
            is_program_valid(["gdrive", "version"])
            if env.GDRIVE == "":
                raise Terminate(f"E: gdrive_path='{env.GDRIVE}' please set a valid path in the cfg.yaml file")

            try:
                check_output, gdrive_gmail = gdrive.check_gdrive_about(gmail)
                if not check_output:
                    log(
                        f"E: provider's registered gmail=[m]{gmail}[/m] does not match with the set gdrive's gmail=[m]{gdrive_gmail}[/m]",
                        is_code=True,
                        h=False,
                    )
                    raise QuietExit
            except Exception as e:
                print_tb(e)
                raise Terminate(e)

        if env.IS_IPFS_USE:
            if not os.path.isfile(env.GPG_PASS_FILE):
                log(f"E: Store your gpg password in the {env.GPG_PASS_FILE}\nfile for decrypting using ipfs")
                raise QuietExit

            if not os.path.isdir(env.IPFS_REPO):
                raise QuietExit(f"E: {env.IPFS_REPO} does not exist")

            start_ipfs_daemon()

        exception_msg = "warning: Given information is not same with the provider's registered info, please update it."
        try:
            flag_error = False
            if provider_info_contract["f_id"] != env.OC_USER:
                log("warning: [m]f_id[/m] does not match with the registered info.")
                log(f"\t{provider_info_contract['f_id']} != {env.OC_USER}")
                flag_error = True

            if env.IS_IPFS_USE:
                gpg_fingerprint = cfg.ipfs.get_gpg_fingerprint(gmail)
                _ipfs_address = get_ipfs_address()
                if provider_info_contract["ipfs_address"] != _ipfs_address:
                    log("warning: [m]ipfs_address[/m] does not match with the registered info.")
                    log(f"\t{provider_info_contract['ipfs_address']} != {_ipfs_address}")
                    flag_error = True

                if provider_info_contract["gpg_fingerprint"] != gpg_fingerprint.upper():
                    log("warning: [m]gpg_fingerprint[/m] does not match with the registered info.")
                    log(f"\t{provider_info_contract['gpg_fingerprint']} != {gpg_fingerprint.upper()}")
                    flag_error = True

            if flag_error:
                raise QuietExit(exception_msg)
        except Exception as e:
            log(f"E: {e}", is_err=True)
            raise QuietExit from e
    except QuietExit as e:
        raise e


class Driver:
    """Driver Class."""

    def __init__(self):
        """Create new Driver object."""
        self.Ebb: "Contract.Contract" = Ebb  # type: ignore
        self.block_number: int = 0
        self.latest_block_number: int = 0
        self.logged_jobs_to_process = None
        self.job_info = None
        self.job_infos = []
        self.logged_job = {}
        self.requester_id: str = ""
        self.storage_duration: List[int] = []
        self.received_block: List[int] = []
        self.is_cached = {}
        #: indicates Lock check for the received job whether received or not
        self.is_provider_received_job = False

    def set_job_recevied_mongodb(self, key, index) -> None:
        if Ebb.mongo_broker.is_received(str(self.requester_id), key, index):
            raise JobException("## [  mongo_db  ] job is already received")

    def is_job_received(self) -> None:
        """Prevent to download job files again."""
        job_infos = self.job_infos[0]
        if job_infos["stateCode"] == state.code["COMPLETED"]:
            raise JobException("## job is already completed")

        if job_infos["stateCode"] == state.code["REFUNDED"]:
            raise JobException("## job is refunded")

        if not job_infos["stateCode"] == state.code["SUBMITTED"]:
            raise JobException("warning: job is already captured and in process or completed")

    def check_requested_job(self) -> None:
        """Check status of the job."""
        if not self.job_infos[0]["core"] or not self.job_infos[0]["run_time"]:
            raise JobException("E: requested job does not exist")

        if not Ebb.does_requester_exist(self.requester_id):
            raise JobException("E: job owner is not registered")

        self.is_job_received()

    def process_logged_job(self, idx):
        """Process logged job one by one."""
        self.storage_duration = []
        self.received_block = []
        wait_until_idle_core_is_available()
        self.is_provider_received_job = True
        console_ruler(idx, character="-")
        job_key = self.logged_job.args["jobKey"]
        index = self.logged_job.args["index"]
        self.job_bn = self.logged_job["blockNumber"]
        self.cloud_storage_id = self.logged_job.args["cloudStorageID"]
        log(f"## job_key=[m]{job_key}[/m] | index={index}")
        log(f"   received_bn={self.job_bn}")
        log(f"   tx_hash={self.logged_job['transactionHash'].hex()} | log_index={self.logged_job['logIndex']}")
        log(f"   provider={self.logged_job.args['provider']}")
        log(f"   received={self.logged_job.args['received']}")
        if self.logged_job["blockNumber"] > self.latest_block_number:
            self.latest_block_number = self.logged_job["blockNumber"]

        try:
            run([env.BASH_SCRIPTS_PATH / "is_str_valid.sh", job_key])
        except Exception as e:
            log(f"E: Filename contains an invalid character: {e}")
            return

        try:
            job_id = 0  # main job_id
            self.job_info = eblocbroker_function_call(
                partial(Ebb.get_job_info, env.PROVIDER_ID, job_key, index, job_id, self.job_bn),
                max_retries=10,
            )
            Ebb.get_job_code_hashes(env.PROVIDER_ID, job_key, index, self.job_bn)
            self.requester_id = self.job_info["job_owner"]
            self.job_info.update({"received_block": self.received_block})
            self.job_info.update({"storage_duration": self.storage_duration})
            self.job_info.update({"cacheType": self.logged_job.args["cacheType"]})
            Ebb.analyze_data(job_key, env.PROVIDER_ID)
            self.job_infos.append(self.job_info)
            log(f"==> requester={self.requester_id}")
            log("==> [yellow]job_info:", "bold")
            log(self.job_info)
        except Exception as e:
            if "Max retries exceeded with url" not in str(e):
                print_tb(e)

            return

        for job in range(1, len(self.job_info["core"])):
            with suppress(Exception):
                self.job_infos.append(  # if workflow is given then add jobs into list
                    Ebb.get_job_info(env.PROVIDER_ID, job_key, index, job, self.job_bn)
                )

        self.check_requested_job()
        # self.set_job_recevied_mongodb(key, index)

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
            "is_cached": self.is_cached,
        }
        if main_cloud_storage_id in (StorageID.IPFS, StorageID.IPFS_GPG):
            storage_class = IpfsClass(**kwargs)
        elif main_cloud_storage_id == StorageID.B2DROP:
            if not config.oc:
                try:
                    eudat.login(env.OC_USER, f"{env.LOG_DIR}/.b2drop_client.txt", env.OC_CLIENT)
                except Exception as e:
                    print_tb(e)
                    sys.exit(1)

            storage_class = B2dropClass(**kwargs)
        elif main_cloud_storage_id == StorageID.GDRIVE:
            storage_class = GdriveClass(**kwargs)

        # run_storage_process(storage_class)
        if cfg.IS_THREADING_ENABLED:
            run_storage_thread(storage_class)
        else:
            storage_class.run()

    def process_logged_jobs(self):
        """Process logged jobs."""
        self.is_cached = {}
        self.latest_block_number = 0
        self.is_provider_received_job = False
        for idx, self.logged_job in enumerate(self.logged_jobs_to_process):
            self.job_infos = []
            self.requester_id = None
            try:
                self.process_logged_job(idx)
                self.sent_job_to_storage_class()
            except JobException as e:
                log(str(e))
            except Exception as e:
                if "Max retries exceeded with url" not in str(e):
                    print_tb(e)

                log(str(e))


def check_block_number_sync(current_bn, bn_read):
    time.sleep(6)
    current_bn = Ebb.get_block_number()
    flag = False
    timeout = time.time() + 60 * 3
    while current_bn < int(bn_read):
        current_bn = Ebb.get_block_number()
        if flag:
            log(f"  {current_bn} -- {int(bn_read)} time={time.time()}", "alert", is_write=False, end="")

        time.sleep(6)
        check_connection(is_silent=True)
        flag = True
        if time.time() > timeout:
            raise Exception(f"Block number stuck at {current_bn}, something is wrong ...")

    return current_bn


def run_driver(given_bn):
    """Run the main driver script for eblocbroker on the background."""
    # dummy sudo command to get the password when session starts for only to
    # create users and submit the slurm job under another user
    run(["sudo", "printf", "hello"])
    kill_process_by_name("gpg-agent")
    # driver_cancel_process = None
    from broker.imports import connect

    connect()
    Ebb: "Contract.Contract" = cfg.Ebb  # type: ignore
    driver = Driver()
    Ebb._is_web3_connected()
    with suppress(Exception):
        log(f"* active_network_id={network.show_active()}")

    if not env.PROVIDER_ID:
        raise Terminate(f"PROVIDER_ID is None in {env.LOG_DIR}/cfg.yaml")

    if not env.WHOAMI or not env.EBLOCPATH or not env.PROVIDER_ID:
        raise Terminate(f"Please run: {env.BASH_SCRIPTS_PATH}/folder_setup.sh")

    if not env.SLURMUSER:
        raise Terminate(f"SLURMUSER is not set in {env.LOG_DIR}/cfg.yaml")

    try:
        deployed_block_number = Ebb.get_deployed_block_number()
    except Exception as e:
        raise e

    if not env.config["block_continue"]:
        env.config["block_continue"] = deployed_block_number

    if given_bn > 0:
        bn_temp = int(given_bn)
    else:
        bn_temp = env.config["block_continue"]
        if not isinstance(env.config["block_continue"], int):
            log("E: block_continue variable is empty or contains an invalid character")
            if not question_yes_no("#> Would you like to read from the contract's deployed block number?"):
                terminate()

            bn_temp = deployed_block_number
            if deployed_block_number:
                env.config["block_continue"] = deployed_block_number
            else:
                raise Terminate(f"deployed_block_number={deployed_block_number} is invalid")

    tools(bn_temp)
    try:
        Ebb.is_contract_exists()
    except:
        terminate(
            "Contract address does not exist on the blockchain, is the blockchain sync?\n"
            f"block_number={Ebb.get_block_number()}",
            is_traceback=False,
        )

    Ebb.is_eth_account_locked(env.PROVIDER_ID)
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
        raise QuietExit(f"provider's ({env.PROVIDER_ID}) ORCID is not verified")

    bn_read = bn_temp
    balance_temp = Ebb.get_balance(env.PROVIDER_ID)
    gwei_balance = Ebb.gwei_balance(env.PROVIDER_ID)
    wei_amount = Decimal(gwei_balance) * (Decimal(10) ** 9)
    # log(f"==> deployed_block_number={deployed_block_number}")
    log(
        f"==> account_balance={math.floor(gwei_balance)} [blue]gwei[/blue] ≈ "
        f"{format(cfg.w3.fromWei(wei_amount, 'ether'), '.2f')} [blue]ether"
    )
    log(f"==> Overall Ebb_token_balance={Cent(balance_temp)._to()} [blue]usd")
    slurm.pending_jobs_check()
    first_iteration_flag = True
    while True:
        wait_until_idle_core_is_available()
        time.sleep(0.2)
        if not str(bn_read).isdigit():
            raise Terminate(f"read_block_from={bn_read}")

        balance = Ebb.get_balance(env.PROVIDER_ID)
        if cfg.IS_THREADING_ENABLED:
            squeue()

        if not first_iteration_flag:
            console_ruler()
            if isinstance(balance, int):
                cc = Cent(int(balance) - int(env.config["token_balance"]))._to()
                log(f"==> since driver started provider_gained_token={cc} usd")

        current_bn = Ebb.get_block_number()
        if not first_iteration_flag:
            log(f" * {get_date()} waiting new job to come since bn={bn_read}")
            log(f"==> current_block={current_bn} | sync_from={bn_read} ", end="")

        if current_bn < int(bn_read):
            time.sleep(6)  # must be updated in 6 seconds
            current_bn = Ebb.get_block_number()
            if current_bn < int(bn_read):
                check_connection()
                msg = f"warning: waiting block number to be updated, it remains constant at {current_bn} < {bn_read}"
                with Halo(text=msg, text_color="yellow", spinner="line", placement="right"):
                    current_bn = check_block_number_sync(current_bn, bn_read)

        bn_read = str(bn_read)  # reading events' block number has been updated
        if not first_iteration_flag:
            slurm.pending_jobs_check()
        else:
            slurm.pending_jobs_check(is_print=False)

        first_iteration_flag = False
        try:
            driver.logged_jobs_to_process = Ebb.run_log_job(bn_read, env.PROVIDER_ID)
            driver.process_logged_jobs()
            if len(driver.logged_jobs_to_process) > 0 and driver.latest_block_number > 0:
                # updates the latest read block number
                bn_read = driver.latest_block_number + 1
                env.config["block_continue"] = bn_read
            if not driver.is_provider_received_job:
                bn_read = env.config["block_continue"] = current_bn
        except Exception as e:
            if "Filter not found" in str(e) or "Read timed out" in str(e):
                # HTTPSConnectionPool(host='core.bloxberg.org', port=443): Read timed out. (read timeout=10)
                try:
                    log()
                    nc(env.BLOXBERG_HOST, 8545)
                except Exception:
                    log(f"E: Failed to make TCP connecton to {env.BLOXBERG_HOST}")
                    # TODO: try with different host? maybe rpc of bloxberg's own host

                first_iteration_flag = True

            log()
            log(f"E: {e}")
            raise e


def reconnect():
    log(f"E: {network.show_active()} is not connected through {env.BLOXBERG_HOST}")
    if cfg.NETWORK_ID == "bloxberg":
        cfg.NETWORK_ID = "bloxberg_core"
    elif cfg.NETWORK_ID == "bloxberg_core":
        with suppress(Exception):
            nc("berg-cmpe-boun.duckdns.org", 8545)
            cfg.NETWORK_ID = "bloxberg"

    log(f"Trying at {cfg.NETWORK_ID} ...")
    network.connect(cfg.NETWORK_ID)


def _run_driver(given_bn, lock):
    config.logging = setup_logger(_log.DRIVER_LOG)
    while True:
        try:
            run_driver(given_bn)
        except HandlerException:
            pass
        except QuietExit as e:
            log(e, is_err=True)
        except zc.lockfile.LockError:
            log(f"E: Driver cannot lock the file {env.DRIVER_LOCKFILE}, the pid file is in use")
        except Terminate as e:
            terminate(str(e), lock)
        except Exception as e:
            if "Max retries exceeded with url" not in str(e):
                print_tb(e)

            if not network.is_connected():
                reconnect()
                if not network.is_connected():
                    time.sleep(15)

            console_ruler(character="*")
            continue
        finally:
            with suppress(Exception):
                if lock:
                    lock.close()


def main(args):
    try:
        given_bn = 0
        if args.bn:
            given_bn = args.bn
        elif args.latest:
            given_bn = Ebb.get_block_number()

        if args.is_thread is False:
            cfg.IS_THREADING_ENABLED = False

        console_ruler("provider session starts", color="white")
        log(f"{datetime.now().strftime('%Y-%m-%d %H:%M')} -- ", h=False, end="")
        log(f"is_threading={cfg.IS_THREADING_ENABLED} -- ", h=False, end="")
        log(f"pid={pid} -- ", h=False, end="")  # driver process pid
        log(f"whoami={env.WHOAMI} -- ", h=False, end="")
        log(f"slurm_user={env.SLURMUSER}", h=False)
        log(f"provider_address: [cy]{env.PROVIDER_ID.lower()}", h=False)
        log(f"rootdir: {os.getcwd()}", h=False)
        log(f"logfile: {_log.DRIVER_LOG}", h=False)
        log(f"Attached to host RPC client listening at '{env.BLOXBERG_HOST}'", h=False)
        print()
        is_driver_on(process_count=1, is_print=False)
        try:
            lock = zc.lockfile.LockFile(env.DRIVER_LOCKFILE, content_template=str(pid))
        except PermissionError:
            print_tb("E: PermissionError is generated for the locked file")
            give_rwe_access(env.WHOAMI, "/tmp/run")
            lock = zc.lockfile.LockFile(env.DRIVER_LOCKFILE, content_template=str(pid))
    except Exception as e:
        print_tb(e)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(1)

    with launch_ipdb_on_exception():  # if an exception is raised, then launch ipdb
        _run_driver(given_bn, lock)

    # finally:
    #     with suppress(Exception):
    #         if lock:
    #             lock.close()
