#!/usr/bin/env python3

import os
import pprint
import subprocess
import sys
import time

import config
import libs.eudat as eudat
import libs.slurm as slurm
from config import bp, load_log  # noqa: F401
from contract.scripts.lib import DataStorage
from contractCalls.does_requester_exist import does_requester_exist
from contractCalls.doesProviderExist import doesProviderExist
from contractCalls.get_balance import get_balance
from contractCalls.get_block_number import get_block_number
from contractCalls.get_deployed_block_number import get_deployed_block_number
from contractCalls.get_job_info import get_job_info
from contractCalls.get_requester_info import get_requester_info
from contractCalls.is_contract_exists import is_contract_exists
from contractCalls.is_web3_connected import is_web3_connected
from contractCalls.LogJob import run_log_job
from driver_eudat import EudatClass
from driver_gdrive import GdriveClass
from driver_ipfs import IpfsClass
from imports import connect
from lib import (
    CacheType,
    StorageID,
    eblocbroker_function_call,
    is_driver_on,
    is_geth_on,
    is_ipfs_running,
    job_state_code,
    log,
    printc,
    run,
    run_command,
    run_whisper_state_receiver,
    session_start_msg,
    terminate,
)
from settings import init_env
from utils import _colorize_traceback, bytes32_to_ipfs, eth_address_to_md5, get_time, read_json

env = init_env()


def startup(slurm_user):
    """ Startup functions are called."""
    session_start_msg(slurm_user)

    if is_driver_on():
        printc("Track output: tail -f ~/.eBlocBroker/transactions/provider.log", "blue")
        sys.exit(1)

    if not is_geth_on():
        sys.exit(1)  # TODO: check to call terminate()

    success = slurm.is_on()
    if not success:
        sys.exit(1)

    # run_driver_cancel()  # TODO: uncomment
    # run_whisper_state_receiver()  # TODO: uncomment
    if env.GDRIVE_USE:
        try:
            run(["gdrive", "version"])
        except:
            logging.warning("Please install gdrive or check its path")
            terminate()

    if env.IPFS_USE:
        is_ipfs_running()

    if env.EUDAT_USE:
        if not env.OC_USER:
            logging.error(f"OC_USER is not set in {env.LOG_PATH}/.env")
            terminate()
        return eudat.login(env.OC_USER, f"{env.LOG_PATH}/eudat_password.txt", f"{env.LOG_PATH}/.oc.pckl")


# dummy sudo command to get the password when session starts for only create users and submit slurm job under another user
subprocess.run(["sudo", "printf", ""])

logging = load_log(f"{env.LOG_PATH}/transactions/provider.log")
config.eBlocBroker, config.w3 = connect()

if not config.eBlocBroker or not config.w3:
    terminate()

columns = 100
yes = set(["yes", "y", "ye"])
no = set(["no", "n"])
oc = None
driver_cancel_process = None
whisper_state_receiver_process = None
_env = os.environ.copy()

if not env.PROVIDER_ID:
    logging.error("PROVIDER_ID is None")
    terminate()

if not env.WHOAMI or not env.EBLOCPATH or not env.PROVIDER_ID:
    logging.warning("Please run: ./folder_setup.sh")
    terminate()

slurm_user = os.getenv("SLURMUSER")
if not slurm_user:
    logging.error("SLURMUSER is not set in .bashrc or .zshrc")
    terminate()

oc = startup(slurm_user)
is_contract_exists = is_contract_exists()
if not is_contract_exists:
    logging.error("Please check that you are using eBlocPOA blockchain")
    terminate()

logging.info(f"is_web3_connected={is_web3_connected()}")
logging.info(f"rootdir={os.getcwd()}")
logging.info(f"whoami={env.WHOAMI}")

try:
    contract = read_json("contractCalls/contract.json")
except:
    logging.error(_colorize_traceback())
    terminate()

contract_address = contract["address"]
logging.info("{0: <18}".format("contract_address:") + contract_address)

if not doesProviderExist(env.PROVIDER_ID):
    logging.error(
        f"E: Your Ethereum address {env.PROVIDER_ID}"
        "does not match with any provider in eBlocBroker. Please register your \n"
        "provider using your Ethereum Address in to the eBlocBroker. You can \n"
        "use 'contractCalls/register_provider.py' script to register your provider."
    )
    terminate()

if not config.eBlocBroker.functions.isOrcIDVerified(env.PROVIDER_ID).call():
    logging.error("E: Provider's orcid is not verified.")
    terminate()

deployed_block_number = get_deployed_block_number()
if not os.path.isfile(env.BLOCK_READ_FROM_FILE):
    f = open(env.BLOCK_READ_FROM_FILE, "w")
    f.write(f"{deployed_block_number}")
    f.close()

f = open(env.BLOCK_READ_FROM_FILE, "r")
block_read_from_local = f.read().strip()
f.close()

if not block_read_from_local.isdigit():
    logging.error("E: BLOCK_READ_FROM_FILE is empty or contains an invalid character")
    logging.info("#> Would you like to read from contract's deployed block number? [Y/n]")
    while True:
        choice = input().lower()
        if choice in yes:
            block_read_from_local = deployed_block_number
            f = open(env.BLOCK_READ_FROM_FILE, "w")
            f.write(deployed_block_number)
            f.close()
            break
        elif choice in no:
            terminate()
        else:
            sys.stdout.warning("Please respond with 'yes' or 'no'")

block_read_from = str(block_read_from_local)
balance_temp = get_balance(env.PROVIDER_ID)
logging.info(f"deployed_block_number={deployed_block_number} balance={balance_temp}")

while True:
    if not str(block_read_from).isdigit():
        logging.error(f"block_read_from={block_read_from}")
        terminate()

    balance = get_balance(env.PROVIDER_ID)
    success, squeue_output = run_command(["squeue"])
    if not success or "squeue: error:" in str(squeue_output):
        logging.error(f"SLURM is not running on the background. Please run: sudo ./runSlurm.sh")
        logging.error(squeue_output)
        terminate()

    idle_cores = slurm.get_idle_cores()
    log(f"Current Slurm Running jobs success:\n {squeue_output}")
    log("-" * int(columns), "green")
    if isinstance(balance, int):
        log(f"[{get_time()}] provider_gained_wei={int(balance) - int(balance_temp)}")

    log(f"[{get_time()}] Waiting new job to come since block number={block_read_from}", "green")
    current_block_number = get_block_number()
    logging.info("Waiting for new block to increment by one.")
    logging.info(f"Current block number={current_block_number} | sync from block number={block_read_from}")
    logging.info(f"is_web3_connected={is_web3_connected()}")
    while current_block_number < int(block_read_from):
        time.sleep(1)
        current_block_number = get_block_number()

    logging.info(f"Passed incremented block number... Continue to wait from block number={block_read_from}")
    block_read_from = str(block_read_from)  # starting reading event's location has been updated
    # block_read_from = '3082590' # used for test purposes
    slurm.pending_jobs_check()
    logged_jobs_to_process = run_log_job(block_read_from, env.PROVIDER_ID)
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
        log(
            f"received_block_number={block_number} \n"
            f"transactionHash={logged_job['transactionHash'].hex()} | log_index={logged_job['logIndex']} \n"
            f"provider={logged_job.args['provider']} \n"
            f"job_key={job_key} \n"
            f"index={index} \n"
            f"received={logged_job.args['received']}",
            "yellow",
        )
        received_block = []
        storageDuration = []
        for idx, source_code_hash_byte in enumerate(logged_job.args["sourceCodeHash"]):
            if idx > 0:
                log("")
            if cloudStorageID[idx] == StorageID.IPFS.value or cloudStorageID[idx] == StorageID.IPFS_MINILOCK.value:
                source_code_hash = bytes32_to_ipfs(source_code_hash_byte)
                if idx == 0 and source_code_hash != job_key:
                    logging.error("E: IPFS hash does not match with the given source_code_hash.")
                    is_break = True
            else:
                source_code_hash = config.w3.toText(source_code_hash_byte)

            ds = DataStorage(config.eBlocBroker, config.w3, env.PROVIDER_ID, source_code_hash_byte)
            received_block.append(ds.received_block)
            storageDuration.append(ds.storage_duration)

            is_already_cached[source_code_hash] = False  # TODO: double check
            # if remaining time to cache is 0, then caching is requested for the related source_code_hash
            if ds.received_block + ds.storage_duration >= block_number:
                if ds.received_block < block_number:
                    is_already_cached[source_code_hash] = True
                elif ds.received_block == block_number:
                    if source_code_hash in is_already_cached:
                        is_already_cached[source_code_hash] = True
                    else:
                        # for the first job should be False since it is requested for cache for the first time
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

        success, str_check = run_command(["bash", f"{env.EBLOCPATH}/str_check.sh", job_key])
        job_infos_to_process = []
        job_id = 0

        try:
            job_info = eblocbroker_function_call(
                lambda: get_job_info(env.PROVIDER_ID, job_key, index, job_id, block_number), 10,
            )
            job_info.update({"received_block": received_block})
            job_info.update({"storageDuration": storageDuration})
            job_info.update({"cacheType": logged_job.args["cacheType"]})
            pprint.pprint(job_info)
            job_infos_to_process.append(job_info)
        except:
            is_break = True

        for job in range(1, len(job_infos_to_process[0]["core"])):
            try:
                job_info = get_job_info(env.PROVIDER_ID, job_key, index, job, block_number)
                job_infos_to_process.append(job_info)  # adds jobs if workflow exists
            except:
                pass
        if (
            is_break
            or not len(job_infos_to_process[0]["core"])
            or not len(job_infos_to_process[0]["executionDuration"])
        ):
            logging.error("E: Requested job does not exist")
            is_break = True
        else:
            logging.info(f"job_owner/requester_id: {job_infos_to_process[0]['jobOwner']}")
            requester_id = job_infos_to_process[0]["jobOwner"].lower()
            is_requester_exist = does_requester_exist(requester_id)
            if job_infos_to_process[0]["jobStateCode"] == job_state_code["COMPLETED"]:
                logging.info("Job is already completed.")
                is_break = True

            if job_infos_to_process[0]["jobStateCode"] == job_state_code["REFUNDED"]:
                logging.info("Job is refunded.")
                is_break = True

            if not is_break and not job_infos_to_process[0]["jobStateCode"] == job_state_code["SUBMITTED"]:
                logging.info("Job is already captured. It is in process or completed.")
                is_break = True

            if "False" in str_check:
                logging.error("Filename contains invalid character.")
                is_break = True

            if not is_requester_exist:
                logging.error("Job owner is not registered.")
                is_break = True
            else:
                try:
                    requester_info = get_requester_info(requester_id)
                except:
                    is_break = True

        if not is_break:
            logging.info("Adding user...")
            success, output = run_command(
                ["sudo", "bash", f"{env.EBLOCPATH}/user.sh", requester_id, env.PROGRAM_PATH, slurm_user,]
            )
            logging.info(output)
            requester_md5_id = eth_address_to_md5(requester_id)
            slurm.pending_jobs_check()
            main_cloud_storage_id = logged_job.args["cloudStorageID"][0]
            if main_cloud_storage_id == StorageID.IPFS.value or main_cloud_storage_id == StorageID.IPFS_MINILOCK.value:
                ipfs = IpfsClass(logged_job, job_infos_to_process, requester_md5_id, is_already_cached,)
                try:
                    ipfs.run()
                except:
                    logging.error(_colorize_traceback())
            elif main_cloud_storage_id == StorageID.EUDAT.value:
                if not oc:
                    eudat.login(env.OC_USER, f"{env.LOG_PATH}/eudat_password.txt", ".oc.pckl")

                eudat = EudatClass(logged_job, job_infos_to_process, requester_md5_id, is_already_cached, oc,)
                eudat.run()
                # thread.start_new_thread(driverFunc.driver_eudat, (logged_job, jobInfo, requester_md5_id))
            elif main_cloud_storage_id == StorageID.GDRIVE.value:
                gdrive = GdriveClass(logged_job, job_infos_to_process, requester_md5_id, is_already_cached,)
                gdrive.run()

    time.sleep(1)
    if len(logged_jobs_to_process) > 0 and int(max_val) > 0:
        # updates the latest read block number
        f_block_read_from = open(env.BLOCK_READ_FROM_FILE, "w")
        block_read_from = int(max_val) + 1
        f_block_read_from.write(f"{block_read_from}")
        f_block_read_from.close()

    # if there is no submitted job for the provider, block start to read from current block number
    if not is_provider_received_job:
        # updates the latest read block number on the file
        f_block_read_from = open(env.BLOCK_READ_FROM_FILE, "w")
        f_block_read_from.write(f"{current_block_number}")
        f_block_read_from.close()
        block_read_from = str(current_block_number)
