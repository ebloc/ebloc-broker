#!/usr/bin/env python3

import sys

import ipfshttpclient

import config
from config import logging
from lib import StorageID
from utils import _colorize_traceback, is_ipfs_running, log  # bytes32_to_ipfs


def is_provider_valid(self, provider):
    if not self.eBlocBroker.functions.doesProviderExist(provider).call():
        raise ValueError(f"E: Requested provider's Ethereum address {provider} does not registered")


def is_requester_valid(self, _from):
    *_, orcid = self.eBlocBroker.functions.getRequesterInfo(_from).call()
    if not self.eBlocBroker.functions.doesRequesterExist(_from).call():
        logging.error(f"\nE: Requester's Ethereum address {_from} is not registered")
        raise

    if not self.eBlocBroker.functions.isOrcIDVerified(_from).call():
        if orcid:
            log(f"E: Requester({_from})'s orcid: {orcid.decode('UTF')} is not verified", "red")
        else:
            log("\nE: Requester({_from})'s orcid is not registered")
        raise


def check_before_submit(self, provider, _from, provider_info, key, job):
    self.is_provider_valid(provider)
    self.is_requester_valid(_from)
    main_storage_id = job.storage_ids[0]
    is_use_ipfs = False
    for storage_id in job.storage_ids:
        if storage_id in (StorageID.IPFS, StorageID.IPFS_GPG):
            is_use_ipfs = True
            break

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

        if job.run_time[idx] == 0:
            logging.error(f"\nE: run_time[{idx}] is provided as 0. Please provide non-zero value")
            raise

    for storage_id in job.storage_ids:
        if storage_id > 4:
            logging.error("\nE: Wrong storage_ids value is given. Please provide from 0 to 4")
            raise

    if len(key) >= 64:
        logging.error("\nE: Length of key is greater than 64, please provide lesser")
        raise

    for core_min in job.run_time:
        if core_min > 1440:
            logging.error("\nE: run_time provided greater than 1440. Please provide smaller value")
            raise

    for cache_type in job.cache_types:
        if cache_type > 1:
            # cache_type = {0: private, 1: public}
            logging.error(f"\nE: cachType ({cache_type}) provided greater than 1. Please provide smaller value")
            raise

    if is_use_ipfs:
        if not is_ipfs_running():
            sys.exit()

        client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001/http")
        # TODO: check is valid IPFS id
        try:
            print(f"trying to connect into {provider_info['ipfs_id']}")
            output = client.swarm.connect(provider_info["ipfs_id"])
            if ("connect" and "success") in str(output):
                log(str(output), "green")
        except:
            _colorize_traceback()
            log("E: connection into provider's IPFS node via swarm is not accomplished")
            sys.exit

    return True

    """ TODO: can it be more than 32 characters
    print(source_code_hashes[0].encode('utf-8'))
    for i in range(len(source_code_hashes)):
        source_code_hashes[i] = source_code_hashes[i]
        if len(source_code_hashes[i]) != 32 and len(source_code_hashes[i]) != 0:
            return False, 'source_code_hashes should be 32 characters.'
    """


def submit_job(self, provider, key, job_price, job, requester=None, account_id=None):
    log("==> Submitting the job")
    provider = self.w3.toChecksumAddress(provider)
    if account_id and not requester:
        _from = self.w3.toChecksumAddress(self.w3.eth.accounts[account_id])
    else:
        _from = requester

    try:
        provider_info = self.get_provider_info(provider)
        log(f"Provider's available_core_num={provider_info['available_core_num']}")
        log(f"Provider's price_core_min={provider_info['price_core_min']}")
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
        job.run_time,
        job.dataTransferOut,
    ]
    try:
        gas_limit = 4500000
        # source_code_hashes_l = []
        # for idx, source_code_hash in job.source_code_hashes:
        #     source_code_hashes_l.append(bytes32_to_ipfs(source_code_hash))
        # log(f"==> source_code_hashes={source_code_hashes_l}")
        tx = self.eBlocBroker.functions.submitJob(
            key, job.data_transfer_ins, args, job.storage_hours, job.source_code_hashes
        ).transact({"from": _from, "value": job_price, "gas": gas_limit})
        return tx.hex()
    except Exception as e:
        if "authentication needed: password or unlock" in getattr(e, "message", repr(e)):
            # https://stackoverflow.com/a/45532289/2402577, https://stackoverflow.com/a/24065533/2402577
            raise config.QuietExit
        raise
