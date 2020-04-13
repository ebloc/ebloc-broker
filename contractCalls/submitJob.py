#!/usr/bin/env python3

import sys

import owncloud

from config import bp, load_log, logging  # noqa: F401
from contract.scripts.lib import cost
from contractCalls.get_provider_info import get_provider_info
from imports import connect
from lib import CacheType, StorageID, get_tx_status, ipfs_add, printc, run_command, silent_remove
from libs.ipfs import mlck_encrypt
from settings import init_env
from utils import _colorize_traceback, generate_md5sum, ipfs_toBytes


def submitJob(
    provider,
    key,
    cores,
    core_execution_durations,
    dataTransferIn_list,
    dataTransferOut,
    storage_id_list,
    source_code_hashes,
    cache_types,
    storage_hours,
    account_id,
    job_price_value,
    data_prices_set_blocknumbers,
):
    eBlocBroker, w3 = connect()

    provider = w3.toChecksumAddress(provider)
    _from = w3.toChecksumAddress(w3.eth.accounts[account_id])

    try:
        provider_info = get_provider_info(provider)
    except:
        print(_colorize_traceback())
        raise

    print(f"Provider's available_core_num={provider_info['availableCoreNum']}")
    print(f"Provider's price_core_min={provider_info['priceCoreMin']}")
    # my_filter = eBlocBroker.events.LogProviderInfo.createFilter(fromBlock=provider_info['blockReadFrom'], toBlock=provider_info['blockReadFrom'] + 1)

    if not eBlocBroker.functions.doesProviderExist(provider).call():
        logging.error(f"E: Requested provider's Ethereum address {provider} does not registered.")
        raise

    blockReadFrom, orcid = eBlocBroker.functions.getRequesterInfo(_from).call()

    if not eBlocBroker.functions.doesRequesterExist(_from).call():
        logging.error(f"E: Requester's Ethereum address {_from} does not exist")
        raise

    if not eBlocBroker.functions.isOrcIDVerified(_from).call():
        logging.error(f"E: Requester's orcid: {orcid.decode('UTF')} is not verified")
        raise

    """
    if StorageID_list.IPFS == storage_id_list or StorageID_list.IPFS_MINILOCK == storage_id_list:
       is_ipfs_running()
       strVal = my_filter.get_all_entries()[0].args['ipfsAddress']nnn
       print('Trying to connect into ' + strVal)
       output = os.popen('ipfs swarm connect ' + strVal).read()
    """

    """
    print(source_code_hashes[0].encode('utf-8'))
    for i in range(len(source_code_hashes)):
        source_code_hashes[i] = source_code_hashes[i]
        if len(source_code_hashes[i]) != 32 and len(source_code_hashes[i]) != 0:
            return False, 'source_code_hashes should be 32 characters.'
    """
    main_storageID = storage_id_list[0]
    if not source_code_hashes:
        logging.error("E: sourceCodeHash list is empty.")
        raise

    if len(key) != 46 and (StorageID.IPFS.value == main_storageID or StorageID.IPFS_MINILOCK.value == main_storageID):
        logging.error(
            "E: key's length does not match with its original length, it should be 46. Please check your key length"
        )
        raise

    if len(key) != 33 and StorageID.GDRIVE.value == main_storageID:
        logging.error(
            "E: key's length does not match with its original length, it should be 33. Please check your key length"
        )
        raise

    for idx, core in enumerate(cores):
        if core > provider_info["availableCoreNum"]:
            logging.error(f"E: Requested {core}, which is {core}, is greater than the provider's core number")
            raise

        if core_execution_durations[idx] == 0:
            logging.error(f"E: core_execution_durations[{idx}] is provided as 0. Please provide non-zero value")
            raise

    for storageID in storage_id_list:
        if storageID > 4:
            logging.error("E: Wrong storage_id_list value is given. Please provide from 0 to 4")
            raise

    if len(key) >= 64:
        logging.error("E: Length of key is greater than 64, please provide lesser")
        raise

    for core_min in core_execution_durations:
        if core_min > 1440:
            logging.error("E: core_execution_durations provided greater than 1440. Please provide smaller value")
            raise

    for cache_type in cache_types:
        if cache_type > 1:
            # cache_type = {0: private, 1: public}
            logging.error(f"E: cachType ({cache_type}) provided greater than 1. Please provide smaller value")
            raise

    # if len(jobDescription) >= 128:
    #    return 'Length of jobDescription is greater than 128, please provide lesser.'
    provider_price_block_number = eBlocBroker.functions.getProviderSetBlockNumbers(provider).call()[-1]
    args = [
        provider,
        provider_price_block_number,
        storage_id_list,
        cache_types,
        data_prices_set_blocknumbers,
        cores,
        core_execution_durations,
        dataTransferOut,
    ]

    try:
        gas_limit = 4500000
        print(str(source_code_hashes))
        tx = eBlocBroker.functions.submitJob(
            key, dataTransferIn_list, args, storage_hours, source_code_hashes
        ).transact({"from": _from, "value": job_price_value, "gas": gas_limit})
        return tx.hex()
    except Exception:
        logging.error(_colorize_traceback)
        raise


if __name__ == "__main__":
    eBlocBroker, w3 = connect()
    env = init_env()

    if len(sys.argv) == 10:
        provider = w3.toChecksumAddress(str(sys.argv[1]))
        key = str(sys.argv[2])
        cores = int(sys.argv[3])
        core_execution_durations = int(sys.argv[4])
        dataTransfer = int(sys.argv[5])
        storage_id_list = int(sys.argv[6])
        sourceCodeHash = str(sys.argv[7])
        storage_hours = int(sys.argv[8])
        account_id = int(sys.argv[9])
    elif len(sys.argv) == 13:
        provider = w3.toChecksumAddress(str(sys.argv[1]))
        key = str(sys.argv[2])
        cores = int(sys.argv[3])
        coreDayDuration = int(sys.argv[4])
        coreHour = int(sys.argv[5])
        core_execution_durations = int(sys.argv[6])
        dataTransferIn = int(sys.argv[7])
        dataTransferOut = int(sys.argv[8])
        storage_id_list = int(sys.argv[9])
        sourceCodeHash = str(sys.argv[10])
        storage_hours = int(sys.argv[11])
        account_id = int(sys.argv[12])
        core_execution_durations = core_execution_durations + coreHour * 60 + coreDayDuration * 1440
    else:
        # requester inputs for testing
        account_id = 1
        provider = w3.toChecksumAddress("0x57b60037b82154ec7149142c606ba024fbb0f991")  # netlab

        storage_id_list = [StorageID.IPFS.value, StorageID.IPFS.value]
        # storage_id_list = [StorageID.IPFS_MINILOCK.value, StorageID.IPFS_MINILOCK.value]
        # storage_id_list = [StorageID.IPFS_MINILOCK.value, StorageID.IPFS.value]

        main_storageID = storage_id_list[0]
        cache_types = [CacheType.PUBLIC.value, CacheType.PUBLIC.value]

        ipfs_dict = {}
        source_code_hashes = []
        folders = []
        md5sums = []
        ipfs_hashes = []
        # full path of the sourceCodeFolders is given
        folders.append(f"{env.EBLOCPATH}/base/sourceCode")
        folders.append(f"{env.EBLOCPATH}/base/data/data1")

        if main_storageID == StorageID.IPFS.value or main_storageID == StorageID.IPFS_MINILOCK.value:
            if main_storageID == StorageID.IPFS.value:
                printc("Submitting source code through IPFS...")

            if main_storageID == StorageID.IPFS_MINILOCK.value:
                printc("Submitting source code through IPFS_MINILOCK...")

            for idx, folder in enumerate(folders):
                target = folder
                if storage_id_list[idx] == StorageID.IPFS_MINILOCK.value:
                    provider_minilock_id = (
                        "SjPmN3Fet4bKSBJAutnAwA15ct9UciNBNYo1BQCFiEjHn"  # TODO: read from the provider
                    )
                    mlck_pass = "bright wind east is pen be lazy usual"
                    success, target = mlck_encrypt(provider_minilock_id, mlck_pass, target)
                    if not success:
                        sys.exit(1)
                    printc(f"minilock_file:{target}", "blue")

                success, ipfs_hash = ipfs_add(target)
                # success, ipfs_hash = ipfs_add(folder, True)  # includes .git/
                success, output = run_command(["ipfs", "refs", ipfs_hash])
                if not success:
                    sys.exit(1)

                # ipfs_dict[ipfs_hash] = md5sums
                ipfs_hashes.append(ipfs_hash)
                md5sum = generate_md5sum(target)
                if idx == 0:
                    key = ipfs_hash

                source_code_hashes.append(ipfs_toBytes(ipfs_hash))
                md5sums.append(md5sum)
                printc(f"{target} \nipfs_hash:{ipfs_hashes[idx]}  md5sum:{md5sums[idx]}\n", "green")
                if main_storageID == StorageID.IPFS_MINILOCK.value:
                    # created .minilock file is removed since its already in ipfs
                    silent_remove(target)
        elif main_storageID == StorageID.EUDAT.value:
            print("Submitting through EUDAT")
            oc = owncloud.Client("https://b2drop.eudat.eu/")
            with open(f"{env.EBLOCPATH}/eudat_password.txt", "r") as content_file:
                password = content_file.read().strip()

            oc.login(env.OC_USER, password)

        cores = [1]
        core_execution_durations = [1]
        storage_hours = [1, 1]
        dataTransferIn_list = [1, 1]  # TODO: calculate from the file itself
        dataTransferOut = 1
        data_prices_set_blocknumbers = [0, 0]

    requester = w3.toChecksumAddress(w3.eth.accounts[account_id])
    job_price_value, _cost = cost(
        cores,
        core_execution_durations,
        provider,
        requester,
        source_code_hashes,
        dataTransferIn_list,
        dataTransferOut,
        storage_hours,
        storage_id_list,
        cache_types,
        data_prices_set_blocknumbers,
        eBlocBroker,
        w3,
        False,
    )

    try:
        output = submitJob(
            provider,
            key,
            cores,
            core_execution_durations,
            dataTransferIn_list,
            dataTransferOut,
            storage_id_list,
            source_code_hashes,
            cache_types,
            storage_hours,
            account_id,
            job_price_value,
            data_prices_set_blocknumbers,
        )
        receipt = get_tx_status(output)
        if receipt["status"] == 1:
            try:
                logs = eBlocBroker.events.LogJob().processReceipt(receipt)
                print(f"Job index={logs[0].args['index']}")
            except IndexError:
                logging.error("E: Transaction is reverted.")
    except:
        print(_colorize_traceback())
        sys.exit(1)
