#!/usr/bin/env python3


import config
from _tools import bp  # noqa: F401
from config import logging
from lib import StorageID
from utils import _colorize_traceback


def check_before_submit(self, provider, _from, provider_info, key, job):
    if not self.eBlocBroker.functions.doesProviderExist(provider).call():
        logging.error(f"\nE: Requested provider's Ethereum address {provider} does not registered.")
        raise

    *_, orcid = self.eBlocBroker.functions.getRequesterInfo(_from).call()
    if not self.eBlocBroker.functions.doesRequesterExist(_from).call():
        logging.error(f"\nE: Requester's Ethereum address {_from} is not registered")
        raise

    if not self.eBlocBroker.functions.isOrcIDVerified(_from).call():
        logging.error(f"\nE: Requester's orcid: {orcid.decode('UTF')} is not verified")
        raise

    """
    if StorageID_list.IPFS == storage_ids or StorageID_list.IPFS_GPG == storage_ids:
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

    main_storage_id = job.storage_ids[0]
    if not job.source_code_hashes:
        logging.error("E: sourceCodeHash list is empty")
        raise

    if len(key) != 46 and main_storage_id in (StorageID.IPFS, StorageID.IPFS_GPG):
        logging.error(
            "\nE: key's length does not match with its original length, it should be 46. Please check your key length"
        )
        raise

    if len(key) != 33 and main_storage_id == StorageID.GDRIVE:
        logging.error(
            "\nE: key's length does not match with its original length, it should be 33. Please check your key length"
        )
        raise

    for idx, core in enumerate(job.cores):
        if core > provider_info["available_core_num"]:
            logging.error(f"\nE: Requested {core}, which is {core}, is greater than the provider's core number")
            raise

        if job.execution_durations[idx] == 0:
            logging.error(f"\nE: execution_durations[{idx}] is provided as 0. Please provide non-zero value")
            raise

    for storage_id in job.storage_ids:
        if storage_id > 4:
            logging.error("\nE: Wrong storage_ids value is given. Please provide from 0 to 4")
            raise

    if len(key) >= 64:
        logging.error("\nE: Length of key is greater than 64, please provide lesser")
        raise

    for core_min in job.execution_durations:
        if core_min > 1440:
            logging.error("\nE: execution_durations provided greater than 1440. Please provide smaller value")
            raise

    for cache_type in job.cache_types:
        if cache_type > 1:
            # cache_type = {0: private, 1: public}
            logging.error(f"\nE: cachType ({cache_type}) provided greater than 1. Please provide smaller value")
            raise


def submit_job(self, provider, key, account_id, job_price, job):
    provider = self.w3.toChecksumAddress(provider)
    _from = self.w3.toChecksumAddress(self.w3.eth.accounts[account_id])

    try:
        provider_info = self.get_provider_info(provider)
        print(f"Provider's available_core_num={provider_info['available_core_num']}")
        print(f"Provider's price_core_min={provider_info['price_core_min']}")
        # my_filter = eBlocBroker.events.LogProviderInfo.createFilter(
        #                                fromBlock=provider_info['block_read_from'],
        #                                toBlock=provider_info['block_read_from'] + 1)
    except:
        _colorize_traceback()
        raise

    self.check_before_submit(provider, _from, provider_info, key, job)

    provider_price_block_number = self.eBlocBroker.functions.getProviderSetBlockNumbers(provider).call()[-1]
    args = [
        provider,
        provider_price_block_number,
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.execution_durations,
        job.dataTransferOut,
    ]
    try:
        gas_limit = 4500000
        print(str(job.source_code_hashes))
        tx = self.eBlocBroker.functions.submitJob(
            key, job.dataTransferIns, args, job.storage_hours, job.source_code_hashes
        ).transact({"from": _from, "value": job_price, "gas": gas_limit})
        return tx.hex()
    except Exception as e:
        if "authentication needed: password or unlock" in getattr(e, "message", repr(e)):
            # https://stackoverflow.com/a/45532289/2402577, https://stackoverflow.com/a/24065533/2402577
            raise config.QuietExit
        raise
