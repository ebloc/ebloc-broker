#!/usr/bin/env python3

import os
import pprint
import sys
import textwrap
import time
from functools import partial

import config
import eblocbroker.Contract as Contract
import libs.eudat as eudat
import libs.slurm as slurm
from config import env, logging, setup_logger
from contract.scripts.lib import DataStorage
from drivers.eudat import EudatClass
from drivers.gdrive import GdriveClass
from drivers.ipfs import IpfsClass
from imports import connect
from lib import job_state_code, run, run_command, run_storage_thread, session_start_msg, terminate
from libs.user_setup import user_add
from startup import bp  # noqa: F401
from utils import (
    CacheType,
    StorageID,
    _colorize_traceback,
    bytes32_to_ipfs,
    eth_address_to_md5,
    get_time,
    is_driver_on,
    is_geth_on,
    is_ipfs_running,
    log,
    no,
    printc,
    read_file,
    read_json,
    write_to_file,
    yes,
)

from lib import eblocbroker_function_call  # noqa: F401; run_whisper_state_receiver,

# from multiprocessing import Process
# from threading import Thread

is_ipfs_running()


def startup(slurm_user, block_number):
    """Startup functions are called."""
    session_start_msg(slurm_user, block_number)
    try:
        is_driver_on()
        is_geth_on()
        slurm.is_on()
    except Exception as e:
        if type(e).__name__ != "QuietExit":
            _colorize_traceback()

        printc("Track output using:")
        printc("tail -f ~/.eBlocBroker/provider.log", "blue")
        sys.exit(1)

    # run_driver_cancel()  # TODO: uncomment
    # run_whisper_state_receiver()  # TODO: uncomment
    if env.GDRIVE_USE:
        try:
            run(["gdrive", "version"])
        except Exception:
            logging.warning("E: Please install gdrive or check its path")
            terminate()

    if env.IPFS_USE:
        is_ipfs_running()

    if env.EUDAT_USE:
        if not env.OC_USER:
            terminate(f"E: OC_USER is not set in {env.LOG_PATH}/.env")
        else:
            eudat.login(env.OC_USER, f"{env.LOG_PATH}/.eudat_provider.txt", env.OC_CLIENT)


# dummy sudo command to get the password when session starts for only to
# create users and submit slurm job under another user
run(["sudo", "printf", ""])

setup_logger(f"{env.LOG_PATH}/provider.log")
columns = 100
driver_cancel_process = None
whisper_state_receiver_process = None

try:
    connect()
    ebb = Contract.eblocbroker
except:
    _colorize_traceback()
    terminate()

if not env.PROVIDER_ID:
    terminate("PROVIDER_ID is None")

if not env.WHOAMI or not env.EBLOCPATH or not env.PROVIDER_ID:
    logging.warning("Please run: ./folder_setup.sh")
    terminate()

slurm_user = os.getenv("SLURMUSER")
if not slurm_user:
    terminate("SLURMUSER is not set in ~/.eBlocBroker/.env")

deployed_block_number = ebb.get_deployed_block_number()
if not os.path.isfile(env.BLOCK_READ_FROM_FILE):
    write_to_file(env.BLOCK_READ_FROM_FILE, deployed_block_number)

block_read_from_local = read_file(env.BLOCK_READ_FROM_FILE)
if not block_read_from_local.isdigit():
    logging.warning("E: BLOCK_READ_FROM_FILE is empty or contains an invalid character")
    logging.info("#> Would you like to read from contract's deployed block number? [Y/n]")
    while True:
        choice = input().lower()
        if choice in yes:
            block_read_from_local = deployed_block_number
            write_to_file(env.BLOCK_READ_FROM_FILE, deployed_block_number)
            break
        elif choice in no:
            terminate()
        else:
            log("Please respond with 'yes' or 'no'")

startup(slurm_user, block_read_from_local)
try:
    ebb.is_contract_exists()
    contract_file = read_json("eblocbroker/contract.json")
except:
    terminate()

log(f"is_web3_connected={ebb.is_web3_connected()}", "blue")
log(f"rootdir={os.getcwd()}", "blue")
log(f"whoami={env.WHOAMI}", "blue")
log("{0: <18}".format("contract_address:") + contract_file["address"], "blue")

if not ebb.does_provider_exist(env.PROVIDER_ID):
    logging.error(
        textwrap.fill(
            "E: Your Ethereum address %s "
            "does not match with any provider in eBlocBroker. Please register your "
            "provider using your Ethereum Address in to the eBlocBroker. You can "
            "use 'eblocbroker/register_provider.py' script to register your provider.",
            env.PROVIDER_ID,
            80,
        )
    )
    terminate()

if not ebb.is_orcid_verified(env.PROVIDER_ID):
    terminate("E: Provider's orcid is not verified")

block_read_from = block_read_from_local
balance_temp = ebb.get_balance(env.PROVIDER_ID)
logging.info("deployed_block_number=%s balance=%s", deployed_block_number, balance_temp)

while True:
    time.sleep(0.1)
    if not str(block_read_from).isdigit():
        terminate(f"block_read_from={block_read_from}")

    balance = ebb.get_balance(env.PROVIDER_ID)
    success, squeue_output = run_command(["squeue"])
    # gets other info after the first line

    if not success or "squeue: error:" in str(squeue_output):
        logging.error("SLURM is not running on the background. Please run:\nsudo ./bash_scripts/run_slurm.sh")
        log(squeue_output, "red")
        terminate()

    idle_cores = slurm.get_idle_cores()
    if len(f"{squeue_output}\n".split("\n", 1)[1]) > 0:
        # checks if the squeue output's line number is gretaer than 1
        log(f"Current slurm running jobs status:\n{squeue_output}")
        log("-" * int(columns), "green")

    if isinstance(balance, int):
        log(f"[{get_time()}] provider_gained_wei={int(balance) - int(balance_temp)}")

    current_block_number = ebb.get_block_number()
    log(f"[{get_time()}] Waiting new job to come since block number={block_read_from}", "blue")
    log(f"[{get_time()}] Waiting for new block to increment by one", "blue")
    log(f"[{get_time()}] current_block={current_block_number} | sync_from={block_read_from}", "blue")

    log(f"[{get_time()}] is_web3_connected={ebb.is_web3_connected()}", "blue")
    while current_block_number < int(block_read_from):
        current_block_number = ebb.get_block_number()
        time.sleep(0.1)

    log(f"Passed incremented block number... Continue to wait from block number={block_read_from}", "yellow")
    # starting reading event's location has been updated
    block_read_from = str(block_read_from)
    slurm.pending_jobs_check()
    logged_jobs_to_process = ebb.run_log_job(block_read_from, env.PROVIDER_ID)
    max_val = 0
    is_provider_received_job = False
    is_already_cached = {}
    for idx, logged_job in enumerate(logged_jobs_to_process):
        is_break = False
        is_provider_received_job = True
        columns_size = int(int(columns) / 2 - 12)
        log("-" * columns_size + f" {idx} " + "-" * columns_size, "blue")
        # sourceCodeHash = binascii.hexlify(logged_job.args['sourceCodeHash'][0]).decode("utf-8")[0:32]
        job_key = logged_job.args["jobKey"]
        index = logged_job.args["index"]
        cloudStorageID = logged_job.args["cloudStorageID"]
        block_number = logged_job["blockNumber"]
        log(f"job_key={job_key} | index={index}", "green")
        log(
            f"received_block_number={block_number} \n"
            f"transactionHash={logged_job['transactionHash'].hex()} | log_index={logged_job['logIndex']} \n"
            f"provider={logged_job.args['provider']} \n"
            f"received={logged_job.args['received']}",
            "yellow",
        )
        received_block = []
        storageDuration = []
        for idx, source_code_hash_byte in enumerate(logged_job.args["sourceCodeHash"]):
            if idx > 0:
                log("")
            if cloudStorageID[idx] in (StorageID.IPFS, StorageID.IPFS_MINILOCK):
                source_code_hash = bytes32_to_ipfs(source_code_hash_byte)
                if idx == 0 and source_code_hash != job_key:
                    logging.error("E: IPFS hash does not match with the given source_code_hash.")
                    is_break = True
            else:
                source_code_hash = config.w3.toText(source_code_hash_byte)

            ds = DataStorage(config.eBlocBroker, config.w3, env.PROVIDER_ID, source_code_hash_byte)
            received_block.append(ds.received_block)
            storageDuration.append(ds.storage_duration)

            is_already_cached[source_code_hash] = False  # FIXME: double check
            # if remaining time to cache is 0, then caching is requested for the related source_code_hash
            if ds.received_block + ds.storage_duration >= block_number:
                if ds.received_block < block_number:
                    is_already_cached[source_code_hash] = True
                elif ds.received_block == block_number:
                    if source_code_hash in is_already_cached:
                        is_already_cached[source_code_hash] = True
                    else:
                        # for the first job should be False since it is
                        # requested for cache for the first time
                        is_already_cached[source_code_hash] = False

            log(
                f"sourceCodeHash[{idx}]={source_code_hash}\n"
                f"received_block={ds.received_block}\n"
                f"storageDuration(block_number)={ds.storage_duration}\n"
                f"cloudStorageID[{idx}]={StorageID(cloudStorageID[idx]).name}\n"
                f"cached_type={CacheType(logged_job.args['cacheType'][idx]).name}\n"
                f"is_already_cached={is_already_cached[source_code_hash]}"
            )

        if logged_job["blockNumber"] > int(max_val):
            max_val = logged_job["blockNumber"]

        try:
            run(["bash", f"{env.EBLOCPATH}/bash_scripts/is_str_valid.sh", job_key])
        except:
            logging.error("E: Filename contains invalid character")
            is_break = True

        job_infos_to_process = []
        job_id = 0
        try:
            job_info = eblocbroker_function_call(
                partial(ebb.get_job_info, env.PROVIDER_ID, job_key, index, job_id, block_number), 10
            )
            job_info.update({"received_block": received_block})
            job_info.update({"storageDuration": storageDuration})
            job_info.update({"cacheType": logged_job.args["cacheType"]})
            log("")
            pprint.pprint(job_info)
            job_infos_to_process.append(job_info)
        except:
            is_break = True

        for job in range(1, len(job_infos_to_process[0]["core"])):
            try:
                job_infos_to_process.append(  # adds jobs if workflow exists
                    ebb.get_job_info(env.PROVIDER_ID, job_key, index, job, block_number)
                )
            except:
                pass

        if is_break or not job_infos_to_process[0]["core"] or not job_infos_to_process[0]["executionDuration"]:
            logging.error("E: Requested job does not exist")
            is_break = True
        else:
            log(f"requester={job_infos_to_process[0]['jobOwner'].lower()}", "yellow")
            requester_id = job_infos_to_process[0]["jobOwner"].lower()
            is_requester_exist = ebb.does_requester_exist(requester_id)
            if job_infos_to_process[0]["jobStateCode"] == job_state_code["COMPLETED"]:
                logging.info("Job is already completed")
                is_break = True

            if job_infos_to_process[0]["jobStateCode"] == job_state_code["REFUNDED"]:
                logging.info("Job is refunded.")
                is_break = True

            if not is_break and not job_infos_to_process[0]["jobStateCode"] == job_state_code["SUBMITTED"]:
                logging.info("Job is already captured. It is in process or completed.")
                is_break = True

            if not is_requester_exist:
                logging.error("E: Job owner is not registered")
                is_break = True
            else:
                try:
                    requester_info = ebb.get_requester_info(requester_id)
                except:
                    is_break = True

        if not is_break:
            try:
                user_add(requester_id, env.PROGRAM_PATH, slurm_user)
                requester_md5_id = eth_address_to_md5(requester_id)
                slurm.pending_jobs_check()
                main_cloud_storage_id = logged_job.args["cloudStorageID"][0]
                if main_cloud_storage_id in (StorageID.IPFS, StorageID.IPFS_MINILOCK):
                    storage_class = IpfsClass(logged_job, job_infos_to_process, requester_md5_id, is_already_cached,)
                elif main_cloud_storage_id == StorageID.EUDAT:
                    if not config.oc:
                        try:
                            eudat.login(env.OC_USER, f"{env.LOG_PATH}/.eudat_provider.txt", env.OC_CLIENT)
                        except:
                            _colorize_traceback()
                            sys.exit(1)  # FIXME: break

                    storage_class = EudatClass(logged_job, job_infos_to_process, requester_md5_id, is_already_cached)
                    # thread.start_new_thread(driverFunc.driver_eudat, (logged_job, jobInfo, requester_md5_id))
                elif main_cloud_storage_id == StorageID.GDRIVE:
                    storage_class = GdriveClass(logged_job, job_infos_to_process, requester_md5_id, is_already_cached,)

                # run_storage_process(storage_class)
                run_storage_thread(storage_class)
                # storage_class.run()
            except:
                sys.exit(1)

    if len(logged_jobs_to_process) > 0 and int(max_val) > 0:
        # updates the latest read block number
        block_read_from = int(max_val) + 1
        write_to_file(env.BLOCK_READ_FROM_FILE, block_read_from)

    if not is_provider_received_job:
        # if there is no submitted job for the provider, block start to read
        # from the current block number updates the latest read block number
        # read from the file
        write_to_file(env.BLOCK_READ_FROM_FILE, current_block_number)
        block_read_from = current_block_number
