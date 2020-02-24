#!/usr/bin/env python3

import hashlib
import json
import os
import pprint
import subprocess
import sys
import time
from pdb import set_trace as bp

import config
from config import logging
from contractCalls.blockNumber import blockNumber
from contractCalls.doesProviderExist import doesProviderExist
from contractCalls.doesRequesterExist import doesRequesterExist
from contractCalls.get_balance import get_balance
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
from lib import (BLOCK_READ_FROM_FILE, EBLOCPATH, EUDAT_USE, HOME, IPFS_USE, LOG_PATH, OC_USER,
                 PROGRAM_PATH, PROVIDER_ID, RPC_PORT, WHOAMI, CacheType, StorageID,
                 convertBytes32ToIpfs, execute_shell_command, get_idle_cores, is_ipfs_running, isSlurmOn,
                 job_state_code, log, terminate)
from lib_owncloud import eudat_login

# Dummy sudo command to get the password when session starts for only create users and submit slurm job under another user
subprocess.run(["sudo", "printf", ""])

config.eBlocBroker, config.w3 = connect()

if config.eBlocBroker is None or config.w3 is None:
    terminate()

oc = None
driver_cancel_process = None
whisper_state_receiver_process = None
my_env = os.environ.copy()


def run_driver_cancel():
    """
    Runs driver_cancel daemon on the background.
    commad: ps aux | grep \'[d]riverCancel\' | grep \'python3\' | wc -l
    """
    p1 = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "[d]riverCancel"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["grep", "python3"], stdin=p2.stdout, stdout=subprocess.PIPE)
    p2.stdout.close()
    p4 = subprocess.Popen(["wc", "-l"], stdin=p3.stdout, stdout=subprocess.PIPE)
    p3.stdout.close()
    out = p4.communicate()[0].decode("utf-8").strip()
    if int(out) == 0:
        # Running driver_cancel.py on the background if it is not already
        config.driver_cancel_process = subprocess.Popen(["python3", "driver_cancel.py"])


def run_whisper_state_receiver():
    """
    Runs driverReceiver daemon on the background.
    """
    if not os.path.isfile(f"{HOME}/.eBlocBroker/whisperInfo.txt"):
        # First time running:
        logging.info("Please first run: scripts/whisperInitialize.py")
        terminate()
    else:
        with open(f"{HOME}/.eBlocBroker/whisperInfo.txt") as json_file:
            data = json.load(json_file)

        kId = data["kId"]
        # publicKey = data["publicKey"]
        if not config.w3.geth.shh.hasKeyPair(kId):
            logging.error("E: Whisper node's private key of a key pair did not match with the given ID")
            logging.warning("Please first run: scripts/whisperInitialize.py")
            terminate()

    # cmd: ps aux | grep \'[d]riverCancel\' | grep \'python3\' | wc -l
    p1 = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "[d]riverReceiver"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["grep", "python"], stdin=p2.stdout, stdout=subprocess.PIPE)
    p2.stdout.close()
    p4 = subprocess.Popen(["wc", "-l"], stdin=p3.stdout, stdout=subprocess.PIPE)
    p3.stdout.close()
    out = p4.communicate()[0].decode("utf-8").strip()
    if int(out) == 0:
        # Running driver_cancel.py on the background
        # TODO: should be '0' to store log at a file and not print output
        config.whisper_state_receiver_process = subprocess.Popen(["python3", "whisperStateReceiver.py"])


def slurmPendingJobCheck():
    """ If there is no idle cores, waits for idle cores to be emerged. """
    idle_cores = get_idle_cores()
    print_flag = 0
    while idle_cores is None:
        if print_flag == 0:
            logging.info("Waiting running jobs to be completed...")
            print_flag = 1

        time.sleep(10)
        idle_cores = get_idle_cores(False)


def isGethOn():
    """ Checks whether geth runs on the background."""
    # cmd: ps aux | grep [g]eth | grep '8545' | wc -l
    p1 = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "[g]eth"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["grep", str(RPC_PORT)], stdin=p2.stdout, stdout=subprocess.PIPE)
    p2.stdout.close()
    p4 = subprocess.Popen(["wc", "-l"], stdin=p3.stdout, stdout=subprocess.PIPE)
    p3.stdout.close()
    out = p4.communicate()[0].decode("utf-8").strip()

    if int(out) == 0:
        logging.error("Geth is not running on the background.")
        terminate()


def isDriverOn():
    """Checks wheather the Driver.py runs on the background."""
    # cmd: ps aux | grep \'[D]river.py\' | grep \'python\' | wc -l
    p1 = subprocess.Popen(["ps", "aux"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["grep", "[D]river.py"], stdin=p1.stdout, stdout=subprocess.PIPE)
    p1.stdout.close()
    p3 = subprocess.Popen(["grep", "python"], stdin=p2.stdout, stdout=subprocess.PIPE)
    p2.stdout.close()
    p4 = subprocess.Popen(["wc", "-l"], stdin=p3.stdout, stdout=subprocess.PIPE)
    p3.stdout.close()
    out = p4.communicate()[0].decode("utf-8").strip()
    if int(out) > 1:
        logging.warning("Driver is already running.")


def startup():
    """ Startup functions are called."""
    oc = None
    isDriverOn()
    isSlurmOn()
    isGethOn()
    # run_driver_cancel()
    run_whisper_state_receiver()
    if EUDAT_USE:
        if OC_USER is None or OC_USER == "":
            logging.error(f"OC_USER is not set in {EBLOCPATH}/.env")
            terminate()

        oc = eudat_login(OC_USER, f"{LOG_PATH}/eudatPassword.txt")

    return oc


def check_programs():
    status, result = execute_shell_command(["gdrive", "version"])
    if not status:
        logging.warning("Please install gDrive or check its path")
        terminate()


# res = subprocess.check_output(['stty', 'size']).decode('utf-8').strip()
# rows = res[0] columns = res[1]
columns = 100
check_programs()
yes = set(["yes", "y", "ye"])
no = set(["no", "n"])
if WHOAMI == "" or EBLOCPATH == "" or PROVIDER_ID == "":
    logging.warning("Please run:  ./initialize.sh")
    terminate()

log("=" * int(int(columns) / 2 - 12) + " provider session starts " + "=" * int(int(columns) / 2 - 12), "blue")

oc = startup()
is_contract_exists = is_contract_exists()
if not is_contract_exists:
    logging.error("Please check that you are using eBlocPOA blockchain")
    terminate()

logging.info(f"is_web3_connected={is_web3_connected()}")
logging.info(f"rootdir: {os.getcwd()}")
contract = json.loads(open("contractCalls/contract.json").read())
contractAddress = contract["address"]
logging.info("{0: <18}".format("contract_address:") + contractAddress)

if IPFS_USE:
    is_ipfs_running()

provider = config.w3.toChecksumAddress(PROVIDER_ID)

if not doesProviderExist(provider):
    logging.error(
        f"E: Your Ethereum address {provider}"
        "does not match with any provider in eBlocBroker. Please register your \n"
        "provider using your Ethereum Address in to the eBlocBroker. You can \n"
        "use 'contractCalls/register_provider.py' script to register your provider."
    )
    terminate()

if not config.eBlocBroker.functions.isOrcIDVerified(provider).call():
    logging.error("E: Provider's orcid is not verified.")
    terminate()

deployed_block_number = get_deployed_block_number()
logging.info("{0: <18}".format("provider_address:") + provider)
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
            f.write(f"{deployed_block_number}")
            f.close()
            break
        elif choice in no:
            terminate()
        else:
            sys.stdout.warning("Please respond with 'yes' or 'no'")

block_read_from = str(block_read_from_local)
balance_temp = get_balance(provider)
logging.info(f"deployed_block_number={deployed_block_number} balance={balance_temp}")

while True:
    if not str(block_read_from).isdigit():
        logging.error(f"block_read_from={block_read_from}")
        terminate()

    balance = get_balance(provider)
    status, squeue_status = execute_shell_command(["squeue"])
    if "squeue: error:" in str(squeue_status):
        logging.error(f"SLURM is not running on the background, please run: sudo ./runSlurm.sh.")
        logging.error(squeue_status)
        terminate()

    idle_cores = get_idle_cores()
    log(f"Current Slurm Running jobs status:\n {squeue_status}")
    log("-" * int(columns), "green")
    if "notconnected" != balance:
        log(f"Current Time: {time.ctime()} | providerGainedWei={int(balance) - int(balance_temp)}")

    log(f"Waiting new job to come since block number={block_read_from}", "green")
    current_block_number = blockNumber()
    logging.info("Waiting for new block to increment by one.")
    logging.info(f"Current block number={current_block_number} | sync from block number={block_read_from}")
    logging.info(f"is_web3_connected={is_web3_connected()}")
    while int(current_block_number) < int(block_read_from):
        time.sleep(1)
        current_block_number = blockNumber()

    logging.info(f"Passed incremented block number... Continue to wait from block number={block_read_from}")
    block_read_from = str(block_read_from)  # Starting reading event's location has been updated
    # block_read_from = '3082590' # used for test purposes
    slurmPendingJobCheck()
    logged_jobs_to_process = run_log_job(block_read_from, provider)
    max_val = 0
    is_provider_received_job = False
    is_already_cached = {}

    for idx, logged_job in enumerate(logged_jobs_to_process):
        is_pass = False
        is_provider_received_job = True

        log("-" * int(int(columns) / 2 - 12) + f" {idx} " + "-" * int(int(columns) / 2 - 12), "blue")
        # sourceCodeHash = binascii.hexlify(logged_job.args['sourceCodeHash'][0]).decode("utf-8")[0:32]
        jobKey = logged_job.args["jobKey"]
        index = logged_job.args["index"]
        cloudStorageID = logged_job.args["cloudStorageID"]
        _blockNumber = logged_job["blockNumber"]

        log(
            f"receivedBlockNumber={_blockNumber} \n"
            f"transactionHash={logged_job['transactionHash'].hex()} | log_index={logged_job['logIndex']} \n"
            f"provider={logged_job.args['provider']} \n"
            f"job_key={jobKey} \n"
            f"index={index} \n"
            f"received={logged_job.args['received']} \n",
            "yellow",
        )
        receivedBlock = []
        storageDuration = []

        for idx, source_code_hash_bytes in enumerate(logged_job.args["sourceCodeHash"]):
            if cloudStorageID == StorageID.IPFS.value or cloudStorageID == StorageID.IPFS_MINILOCK.value:
                sourceCodeHash = convertBytes32ToIpfs(source_code_hash_bytes)
            else:
                sourceCodeHash = config.w3.toText(source_code_hash_bytes)

            # _storageDuration is received as hour should be converted into blocknumber as multiplying with 240
            job_storage_time = config.eBlocBroker.functions.getJobStorageTime(
                config.w3.toChecksumAddress(provider), source_code_hash_bytes
            ).call()
            _received_block = job_storage_time[0]
            _storageDuration = job_storage_time[1]
            _isPrivate = job_storage_time[2]
            _isVerified_Used = job_storage_time[3]

            receivedBlock.append(_received_block)
            storageDuration.append(_storageDuration)

            # If remaining time to cache is 0, then caching is requested for the related sourceCodeHash
            if _received_block + _storageDuration * 240 >= _blockNumber:
                if _received_block < _blockNumber:
                    is_already_cached[sourceCodeHash] = True
                elif _received_block == _blockNumber:
                    if sourceCodeHash in is_already_cached:
                        is_already_cached[sourceCodeHash] = True
                    else:
                        # For the first job should be False since it is requested for cache for the first time
                        is_already_cached[sourceCodeHash] = False
            else:
                is_already_cached[sourceCodeHash] = False

            log(
                f"sourceCodeHash[{idx}]={sourceCodeHash} \n"
                f"receivedBlock={_received_block} \n"
                f"storageDuration(Hour)={_storageDuration} \n"
                f"cloudStorageID[{idx}]={StorageID(cloudStorageID[idx]).name} \n"
                f"cached_type={CacheType(logged_job.args['cacheType'][idx]).name} \n"
                f"is_already_cached={is_already_cached[sourceCodeHash]} \n"
            )

        if (
            logged_job.args["cloudStorageID"] == StorageID.IPFS
            or logged_job.args["cloudStorageID"] == StorageID.IPFS_MINILOCK
        ):
            sourceCodeHash = convertBytes32ToIpfs(logged_job.args["sourceCodeHash"])
            if sourceCodeHash != logged_job.args["jobKey"]:
                logging.error("IPFS hash does not match with the given sourceCodeHash.")
                is_pass = True

        if logged_job["blockNumber"] > int(max_val):
            max_val = logged_job["blockNumber"]

        if logged_job.args["cloudStorageID"] == StorageID.GITHUB.value:
            status, str_check = execute_shell_command(["bash", f"{EBLOCPATH}/str_check.sh", jobKey.replace("=", "", 1)])
        else:
            status, str_check = execute_shell_command(["bash", f"{EBLOCPATH}/str_check.sh", jobKey])

        job_info = []
        jobID = 0
        for attempt in range(10):
            status, _jobInfo = get_job_info(provider, jobKey, index, jobID, _blockNumber)
            if not status:
                print(_jobInfo)

            _jobInfo.update({"receivedBlock": receivedBlock})
            _jobInfo.update({"storageDuration": storageDuration})
            _jobInfo.update({"cacheType": logged_job.args["cacheType"]})
            pprint.pprint(_jobInfo)
            job_info.append(_jobInfo)
            if status:
                break
            else:
                logging.error(f"E: {job_info}")
                time.sleep(1)
        else:
            is_pass = True
            break

        for job in range(1, len(job_info[0]["core"])):
            _jobInfo = get_job_info(provider, jobKey, index, job, _blockNumber)
            if _jobInfo is not None:
                job_info.append(_jobInfo)  # Adding jobs if workflow exist

        requesterID = ""
        if is_pass or len(job_info[0]["core"]) == 0 or len(job_info[0]["executionDuration"]) == 0:
            logging.error("Requested job does not exist")
            is_pass = True
        else:
            logging.info(f"jobOwner/requesterID: {job_info[0]['jobOwner']}")
            requesterID = job_info[0]["jobOwner"].lower()
            is_requester_exist = doesRequesterExist(requesterID)
            if job_info[0]["jobStateCode"] == job_state_code["COMPLETED"]:
                logging.info("Job is already completed.")
                is_pass = True

            if job_info[0]["jobStateCode"] == job_state_code["REFUNDED"]:
                logging.info("Job is refunded.")
                is_pass = True

            if not is_pass and not job_info[0]["jobStateCode"] == job_state_code["SUBMITTED"]:
                logging.info("Job is already captured. It is in process or completed.")
                is_pass = True

            if "False" in str_check:
                logging.error("Filename contains invalid character")
                is_pass = True

            if not is_requester_exist:
                logging.error("Job owner is not registered")
                is_pass = True
            else:
                status, requesterInfo = get_requester_info(requesterID)

        if not is_pass:
            logging.info("Adding user...")
            status, res = execute_shell_command(["sudo", "bash", f"{EBLOCPATH}/user.sh", requesterID, PROGRAM_PATH])
            logging.info(res)
            requesterIDmd5 = hashlib.md5(requesterID.encode("utf-8")).hexdigest()
            slurmPendingJobCheck()
            main_cloud_storage_id = logged_job.args["cloudStorageID"][0]
            if main_cloud_storage_id == StorageID.IPFS.value or main_cloud_storage_id == StorageID.IPFS_MINILOCK.value:
                ipfs = IpfsClass(logged_job, job_info, requesterIDmd5, is_already_cached)
                ipfs.run()
            elif main_cloud_storage_id == StorageID.EUDAT.value:
                if oc is None:
                    eudat_login()

                eudat = EudatClass(logged_job, job_info, requesterIDmd5, is_already_cached, oc)
                eudat.run()
                # thread.start_new_thread(driverFunc.driver_eudat, (logged_job, jobInfo, requesterIDmd5))
            elif main_cloud_storage_id == StorageID.GDRIVE.value:
                gdrive = GdriveClass(logged_job, job_info, requesterIDmd5, is_already_cached)
                gdrive.run()

    time.sleep(1)
    if len(logged_jobs_to_process) > 0 and int(max_val) != 0:
        f_block_read_from = open(BLOCK_READ_FROM_FILE, "w")  # Updates the latest read block number
        block_read_from = int(max_val) + 1
        f_block_read_from.write(f"{block_read_from}")
        f_block_read_from.close()

    # If there is no submitted job for the provider, block start to read from current block number
    if not is_provider_received_job:
        f_block_read_from = open(BLOCK_READ_FROM_FILE, "w")  # Updates the latest read block number
        f_block_read_from.write(f"{current_block_number}")
        f_block_read_from.close()
        block_read_from = str(current_block_number)
