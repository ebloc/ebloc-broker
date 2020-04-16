#!/usr/bin/env python3


from config import bp, logging  # noqa: F401
from contractCalls.get_provider_info import get_provider_info
from imports import connect
from lib import StorageID
from utils import _colorize_traceback

eBlocBroker, w3 = connect()


def check_before_submit(provider, _from, provider_info, key, job):
    if not eBlocBroker.functions.doesProviderExist(provider).call():
        logging.error(f"E: Requested provider's Ethereum address {provider} does not registered.")
        raise

    block_read_from, orcid = eBlocBroker.functions.getRequesterInfo(_from).call()
    if not eBlocBroker.functions.doesRequesterExist(_from).call():
        logging.error(f"E: Requester's Ethereum address {_from} does not exist")
        raise

    if not eBlocBroker.functions.isOrcIDVerified(_from).call():
        logging.error(f"E: Requester's orcid: {orcid.decode('UTF')} is not verified")
        raise

    """
    if StorageID_list.IPFS == storage_ids or StorageID_list.IPFS_MINILOCK == storage_ids:
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
    # if len(jobDescription) >= 128:
    #    return 'Length of jobDescription is greater than 128, please provide lesser.'

    main_storageID = job.storage_ids[0]
    if not job.source_code_hashes:
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

    for idx, core in enumerate(job.cores):
        if core > provider_info["availableCoreNum"]:
            logging.error(f"E: Requested {core}, which is {core}, is greater than the provider's core number")
            raise

        if job.core_execution_durations[idx] == 0:
            logging.error(f"E: core_execution_durations[{idx}] is provided as 0. Please provide non-zero value")
            raise

    for storageID in job.storage_ids:
        if storageID > 4:
            logging.error("E: Wrong storage_ids value is given. Please provide from 0 to 4")
            raise

    if len(key) >= 64:
        logging.error("E: Length of key is greater than 64, please provide lesser")
        raise

    for core_min in job.core_execution_durations:
        if core_min > 1440:
            logging.error("E: core_execution_durations provided greater than 1440. Please provide smaller value")
            raise

    for cache_type in job.cache_types:
        if cache_type > 1:
            # cache_type = {0: private, 1: public}
            logging.error(f"E: cachType ({cache_type}) provided greater than 1. Please provide smaller value")
            raise


def submitJob(provider, key, account_id, job_price, job):
    provider = w3.toChecksumAddress(provider)
    _from = w3.toChecksumAddress(w3.eth.accounts[account_id])

    try:
        provider_info = get_provider_info(provider)
        print(f"Provider's available_core_num={provider_info['availableCoreNum']}")
        print(f"Provider's price_core_min={provider_info['priceCoreMin']}")
        # my_filter = eBlocBroker.events.LogProviderInfo.createFilter(fromBlock=provider_info['block_read_from'], toBlock=provider_info['block_read_from'] + 1)
    except:
        print(_colorize_traceback())
        raise

    check_before_submit(provider, _from, provider_info, key, job)

    provider_price_block_number = eBlocBroker.functions.getProviderSetBlockNumbers(provider).call()[-1]
    args = [
        provider,
        provider_price_block_number,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.core_execution_durations,
        job.dataTransferOut,
    ]
    try:
        gas_limit = 4500000
        print(str(job.source_code_hashes))
        tx = eBlocBroker.functions.submitJob(
            key, job.dataTransferIns, args, job.storage_hours, job.source_code_hashes
        ).transact({"from": _from, "value": job_price, "gas": gas_limit})
        return tx.hex()
    except Exception:
        logging.error(_colorize_traceback)
        raise
