#!/usr/bin/env python3

import os
import pprint
import subprocess
import sys
import time

import config
from config import EBLOCPATH, load_log
from contract.scripts.lib import DataStorage
from contractCalls.doesProviderExist import doesProviderExist
from contractCalls.doesRequesterExist import doesRequesterExist
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
from lib import (BLOCK_READ_FROM_FILE, EUDAT_USE, HOME, IPFS_USE, LOG_PATH,
                 OC_USER, PROGRAM_PATH, PROVIDER_ID, WHOAMI, CacheType,
                 StorageID, is_driver_on, is_geth_on, is_ipfs_running,
                 is_process_on, job_state_code, log, printc, run_command,
                 terminate)
from lib_owncloud import eudat_login
from lib_slurm import get_idle_cores, is_slurm_on, slurm_pending_jobs_check
from utils import bytes32_to_ipfs, eth_address_to_md5, read_json

# Dummy sudo command to get the password when session starts for only create users and submit slurm job under another user
subprocess.run(["sudo", "printf", ""])

logging = load_log(f"{LOG_PATH}/transactions/providerOut.txt")

config.eBlocBroker, config.w3 = connect()

if config.eBlocBroker is None or config.w3 is None:
    terminate()

oc = None
driver_cancel_process = None
whisper_state_receiver_process = None
my_env = os.environ.copy()

if not PROVIDER_ID:
    logging.error("PROVIDER_ID is None")
    terminate()


def run_driver_cancel():
    """Runs driver_cancel daemon on the background."""
    if not is_process_on("python.*[d]riverCancel", "driverCancel"):
        # Running driver_cancel.py on the background if it is not already
        config.driver_cancel_process = subprocess.Popen(["python3", "driver_cancel.py"])


def run_whisper_state_receiver():
    """Runs driverReceiver daemon on the background."""
    if not os.path.isfile(f"{HOME}/.eBlocBroker/whisperInfo.txt"):
        # First time running:
        logging.info(f"run: {EBLOCPATH}/scripts/whisperInitialize.py")
        terminate()
    else:
        success, data = read_json(f"{HOME}/.eBlocBroker/whisperInfo.txt")
        kId = {}
        if success:
            kId = data["kId"]

        if not success or not config.w3.geth.shh.hasKeyPair(kId):
            logging.error("E: Whisper node's private key of a key pair did not match with the given ID")
            logging.warning("Please first run: scripts/whisperInitialize.py")
            terminate()

    if not is_process_on("python.*[d]riverReceiver", "driverReceiver"):
        # Running driver_cancel.py on the background
        # TODO: should be '0' to store log at a file and not print output
        config.whisper_state_receiver_process = subprocess.Popen(["python3", "whisperStateReceiver.py"])


def startup():
    """ Startup functions are called."""
    oc = None
    if is_driver_on():
        printc("Track output: tail -f ~/.eBlocBroker/transactions/providerOut.txt", "blue")
        sys.exit(1)

    if not is_geth_on():
        sys.exit(1)  # TODO: check to call terminate()

    success = is_slurm_on()
    if not success:
        sys.exit(1)

    # run_driver_cancel()
    run_whisper_state_receiver()
    if EUDAT_USE:
        if OC_USER is None or OC_USER == "":
            logging.error(f"OC_USER is not set in {EBLOCPATH}/.env")
            terminate()

        oc = eudat_login(OC_USER, f"{LOG_PATH}/eudat_password.txt", ".oc.pckl")

    return oc


def check_programs():
    success, output = run_command(["gdrive", "version"])
    if not success:
        logging.warning("Please install gdrive or check its path")
        terminate()

    if IPFS_USE:
        is_ipfs_running()


# output = subprocess.check_output(['stty', 'size']).decode('utf-8').strip()
# rows = output[0] columns = output[1]
columns = 100
check_programs()
yes = set(["yes", "y", "ye"])
no = set(["no", "n"])
if WHOAMI == "" or EBLOCPATH == "" or PROVIDER_ID == "":
    logging.warning("Please run: ./folder_setup.sh")
    terminate()

log(
    "=" * int(int(columns) / 2 - 12) + " provider session starts " + "=" * int(int(columns) / 2 - 12), "cyan",
)

oc = startup()
is_contract_exists = is_contract_exists()
if not is_contract_exists:
    logging.error("Please check that you are using eBlocPOA blockchain")
    terminate()

logging.info(f"is_web3_connected={is_web3_connected()}")
logging.info(f"rootdir: {os.getcwd()}")

success, contract = read_json("contractCalls/contract.json")
if not success:
    terminate()
contractAddress = contract["address"]
logging.info("{0: <18}".format("contract_address:") + contractAddress)

if not doesProviderExist(PROVIDER_ID):
    logging.error(
        f"E: Your Ethereum address {PROVIDER_ID}"
        "does not match with any provider in eBlocBroker. Please register your \n"
        "provider using your Ethereum Address in to the eBlocBroker. You can \n"
        "use 'contractCalls/register_provider.py' script to register your provider."
    )
    terminate()

if not config.eBlocBroker.functions.isOrcIDVerified(PROVIDER_ID).call():
    logging.error("E: Provider's orcid is not verified.")
    terminate()

deployed_block_number = get_deployed_block_number()
logging.info("{0: <18}".format("provider_address:") + PROVIDER_ID)
if not os.path.isfile(BLOCK_READ_FROM_FILE):
    f = open(BLOCK_READ_FROM_FILE, "w")
    f.write(f"{deployed_block_number}")
    f.close()

f = open(BLOCK_READ_FROM_FILE, "r")
block_read_from_local = f.read().strip()
f.close()

if not block_read_from_local.isdigit():
    logging.error("E: BLOCK_READ_FROM_FILE is empty or contains an invalid character")
    logging.info("#> Would you like to read from contract's deployed block number? y/n")
    while True:
        choice = input().lower()
        if choice in yes:
            block_read_from_local = deployed_block_number
            f = open(BLOCK_READ_FROM_FILE, "w")
            f.write(deployed_block_number)
            f.close()
            break
        elif choice in no:
            terminate()
        else:
            sys.stdout.warning("Please respond with 'yes' or 'no'")

block_read_from = str(block_read_from_local)
balance_temp = get_balance(PROVIDER_ID)
logging.info(f"deployed_block_number={deployed_block_number} balance={balance_temp}")

while True:
    if not str(block_read_from).isdigit():
        logging.error(f"block_read_from={block_read_from}")
        terminate()

    balance = get_balance(PROVIDER_ID)
    success, squeue_output = run_command(["squeue"])
    if "squeue: error:" in str(squeue_output):
        logging.error(f"SLURM is not running on the background, please run: sudo ./runSlurm.sh.")
        logging.error(squeue_output)
        terminate()

    idle_cores = get_idle_cores()
    log(f"Current Slurm Running jobs success:\n {squeue_output}")
    log("-" * int(columns), "green")
    if "notconnected" != balance:
        log(f"Current Time: {time.ctime()} | provider_gained_wei={int(balance) - int(balance_temp)}")

    log(f"Waiting new job to come since block number={block_read_from}", "green")
    current_block_number = get_block_number()
    logging.info("Waiting for new block to increment by one.")
    logging.info(f"Current block number={current_block_number} | sync from block number={block_read_from}")
    logging.info(f"is_web3_connected={is_web3_connected()}")
    while current_block_number < int(block_read_from):
        time.sleep(1)
        current_block_number = get_block_number()

    logging.info(f"Passed incremented block number... Continue to wait from block number={block_read_from}")
    block_read_from = str(block_read_from)  # Starting reading event's location has been updated
    # block_read_from = '3082590' # used for test purposes
    slurm_pending_jobs_check()
    logged_jobs_to_process = run_log_job(block_read_from, PROVIDER_ID)
    max_val = 0
    is_provider_received_job = False
    is_already_cached = {}

    for idx, logged_job in enumerate(logged_jobs_to_process):
        is_pass = False
        is_provider_received_job = True

        log(
            "-" * int(int(columns) / 2 - 12) + f" {idx} " + "-" * int(int(columns) / 2 - 12), "blue",
        )
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
            f"received={logged_job.args['received']} \n",
            "yellow",
        )
        received_block = []
        storageDuration = []
        for idx, source_code_hash_byte in enumerate(logged_job.args["sourceCodeHash"]):
            if cloudStorageID[idx] == StorageID.IPFS.value or cloudStorageID[idx] == StorageID.IPFS_MINILOCK.value:
                source_code_hash = bytes32_to_ipfs(source_code_hash_byte)
            else:
                source_code_hash = config.w3.toText(source_code_hash_byte)

            ds = DataStorage(config.eBlocBroker, config.w3, PROVIDER_ID, source_code_hash_byte)
            received_block.append(ds.received_block)
            storageDuration.append(ds.storage_duration)

            is_already_cached[source_code_hash] = False  # TODO: double check
            # If remaining time to cache is 0, then caching is requested for the related sourceCodeHash
            if ds.received_block + ds.storage_duration >= block_number:
                if ds.received_block < block_number:
                    is_already_cached[source_code_hash] = True
                elif ds.received_block == block_number:
                    if source_code_hash in is_already_cached:
                        is_already_cached[source_code_hash] = True
                    else:
                        # For the first job should be False since it is requested for cache for the first time
                        is_already_cached[source_code_hash] = False

            log(
                f"sourceCodeHash[{idx}]={source_code_hash} \n"
                f"received_block={ds.received_block} \n"
                f"storageDuration(block_number)={ds.storage_duration} \n"
                f"cloudStorageID[{idx}]={StorageID(cloudStorageID[idx]).name} \n"
                f"cached_type={CacheType(logged_job.args['cacheType'][idx]).name} \n"
                f"is_already_cached={is_already_cached[source_code_hash]} \n"
            )

        if (
            logged_job.args["cloudStorageID"] == StorageID.IPFS
            or logged_job.args["cloudStorageID"] == StorageID.IPFS_MINILOCK
        ):
            sourceCodeHash = bytes32_to_ipfs(logged_job.args["sourceCodeHash"])
            if sourceCodeHash != logged_job.args["jobKey"]:
                logging.error("IPFS hash does not match with the given sourceCodeHash.")
                is_pass = True

        if logged_job["blockNumber"] > int(max_val):
            max_val = logged_job["blockNumber"]

        if logged_job.args["cloudStorageID"] == StorageID.GITHUB.value:
            success, str_check = run_command(["bash", f"{EBLOCPATH}/str_check.sh", job_key.replace("=", "", 1)])
        else:
            success, str_check = run_command(["bash", f"{EBLOCPATH}/str_check.sh", job_key])

        job_infos_to_process = []
        job_id = 0
        for attempt in range(10):
            success, job_info = get_job_info(PROVIDER_ID, job_key, index, job_id, block_number)
            if not success:
                print(job_info)

            job_info.update({"received_block": received_block})
            job_info.update({"storageDuration": storageDuration})
            job_info.update({"cacheType": logged_job.args["cacheType"]})
            pprint.pprint(job_info)
            job_infos_to_process.append(job_info)
            if success:
                break
            else:
                logging.error(f"E: {job_infos_to_process}")
                time.sleep(1)
        else:
            is_pass = True
            break

        for job in range(1, len(job_infos_to_process[0]["core"])):
            job_info = get_job_info(PROVIDER_ID, job_key, index, job, block_number)
            if job_info is not None:
                job_infos_to_process.append(job_info)  # Adding jobs if workflow exist

        requester_id = ""
        if (
            is_pass
            or len(job_infos_to_process[0]["core"]) == 0
            or len(job_infos_to_process[0]["executionDuration"]) == 0
        ):
            logging.error("Requested job does not exist")
            is_pass = True
        else:
            logging.info(f"jobOwner/requester_id: {job_infos_to_process[0]['jobOwner']}")
            requester_id = job_infos_to_process[0]["jobOwner"].lower()
            is_requester_exist = doesRequesterExist(requester_id)
            if job_infos_to_process[0]["jobStateCode"] == job_state_code["COMPLETED"]:
                logging.info("Job is already completed.")
                is_pass = True

            if job_infos_to_process[0]["jobStateCode"] == job_state_code["REFUNDED"]:
                logging.info("Job is refunded.")
                is_pass = True

            if not is_pass and not job_infos_to_process[0]["jobStateCode"] == job_state_code["SUBMITTED"]:
                logging.info("Job is already captured. It is in process or completed.")
                is_pass = True

            if "False" in str_check:
                logging.error("Filename contains invalid character")
                is_pass = True

            if not is_requester_exist:
                logging.error("Job owner is not registered")
                is_pass = True
            else:
                success, requesterInfo = get_requester_info(requester_id)

        if not is_pass:
            logging.info("Adding user...")
            success, output = run_command(["sudo", "bash", f"{EBLOCPATH}/user.sh", requester_id, PROGRAM_PATH])
            logging.info(output)
            requester_md5_id = eth_address_to_md5(requester_id)
            slurm_pending_jobs_check()
            main_cloud_storage_id = logged_job.args["cloudStorageID"][0]
            if main_cloud_storage_id == StorageID.IPFS.value or main_cloud_storage_id == StorageID.IPFS_MINILOCK.value:
                ipfs = IpfsClass(logged_job, job_infos_to_process, requester_md5_id, is_already_cached,)
                ipfs.run()
            elif main_cloud_storage_id == StorageID.EUDAT.value:
                if oc is None:
                    eudat_login(OC_USER, f"{LOG_PATH}/eudat_password.txt", ".oc.pckl")

                eudat = EudatClass(logged_job, job_infos_to_process, requester_md5_id, is_already_cached, oc,)
                eudat.run()
                # thread.start_new_thread(driverFunc.driver_eudat, (logged_job, jobInfo, requester_md5_id))
            elif main_cloud_storage_id == StorageID.GDRIVE.value:
                gdrive = GdriveClass(logged_job, job_infos_to_process, requester_md5_id, is_already_cached,)
                gdrive.run()

    time.sleep(1)
    if len(logged_jobs_to_process) > 0 and int(max_val) != 0:
        f_block_read_from = open(BLOCK_READ_FROM_FILE, "w")  # Updates the latest read block number
        block_read_from = int(max_val) + 1
        f_block_read_from.write(f"{block_read_from}")
        f_block_read_from.close()

    # If there is no submitted job for the provider, block start to read from current block number
    if not is_provider_received_job:
        # Updates the latest read block number on the file
        f_block_read_from = open(BLOCK_READ_FROM_FILE, "w")
        f_block_read_from.write(f"{current_block_number}")
        f_block_read_from.close()
        block_read_from = str(current_block_number)
