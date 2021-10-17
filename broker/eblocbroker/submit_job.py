#!/usr/bin/env python3

import sys

import broker.cfg as cfg
import broker.config as config
from broker._utils._log import br
from broker._utils.tools import log, print_tb
from broker.config import env, logging
from broker.lib import StorageID
from broker.utils import is_ipfs_on, is_transaction_valid  # bytes32_to_ipfs,
from brownie.exceptions import TransactionError


def is_provider_valid(self, provider):
    provider = self.w3.toChecksumAddress(provider)
    if not self.does_provider_exist(provider):
        raise ValueError(f"Requested provider's Ethereum address {provider} does not registered")


def is_requester_valid(self, _from):
    _from = self.w3.toChecksumAddress(_from)
    *_, orcid = self._get_requester_info(_from)
    if not self.does_requester_exist(_from):
        log(f"E: Requester's Ethereum address {_from} is not registered")
        raise

    if not self._is_orc_id_verified(_from):
        if orcid:
            log(f"E: Requester({_from})'s orcid: {orcid.decode('UTF')} is not verified")
        else:
            log(f"E: Requester({_from})'s orcid is not registered")
        raise


def check_before_submit(self, provider, _from, provider_info, key, job):
    """Check job's conditions before submitting."""
    self.is_provider_valid(provider)
    self.is_requester_valid(_from)
    main_storage_id = job.storage_ids[0]
    is_use_ipfs = False
    for storage_id in job.storage_ids:
        if storage_id > 4:
            logging.error("\nE: Wrong storage_ids value is given. Please provide from 0 to 4")
            raise

        if storage_id in [StorageID.IPFS, StorageID.IPFS_GPG]:
            is_use_ipfs = True
            break

    if not job.source_code_hashes:
        logging.error("E: source_code_hash list is empty")
        raise

    if len(key) >= 64:
        logging.error("\nE: Length of key is greater than 64, please provide lesser")
        raise

    key_len = 46
    if len(key) != key_len and main_storage_id in [StorageID.IPFS, StorageID.IPFS_GPG]:
        logging.error(
            f"\nE: key's length does not match with its original length, it should be {key_len}. Please check your key length"
        )
        raise

    key_len = 33
    if len(key) != 33 and main_storage_id == StorageID.GDRIVE:
        logging.error(
            f"\nE: key's length does not match with its original length, it should be {key_len}. Please check your key length"
        )
        raise

    for idx, core in enumerate(job.cores):
        if core > provider_info["available_core_num"]:
            logging.error(f"\nE: Requested {core}, which is {core}, is greater than the provider's core number")
            raise

        if job.run_time[idx] == 0:
            logging.error(f"\nE: run_time{br(idx)} is provided as 0. Please provide non-zero value")
            raise

    for core_min in job.run_time:
        if core_min > 1440:
            logging.error("\nE: run_time provided greater than 1440. Please provide smaller value")
            raise

    for cache_type in job.cache_types:
        if cache_type > 1:
            # cache_type = {0: private, 1: public}
            logging.error(f"\nE: cache_type ({cache_type}) provided greater than 1. Please provide smaller value")
            raise

    if is_use_ipfs:
        if not is_ipfs_on():
            sys.exit()

        try:
            cfg.ipfs.swarm_connect(provider_info["ipfs_id"])
            # TODO
        except:
            pass

    return True

    """ TODO: can it be more than 32 characters
    print(source_code_hashes[0].encode('utf-8'))
    for i in range(len(source_code_hashes)):
        source_code_hashes[i] = source_code_hashes[i]
        if len(source_code_hashes[i]) != 32 and len(source_code_hashes[i]) != 0:
            return False, 'source_code_hashes should be 32 characters.'
    """


def submit_job(self, provider, key, job_price, job, requester=None, account_id=None):
    """Submit job."""
    if not requester and not account_id:
        raise Exception("E: Not valid msg.sender address is provided.")

    log("==> Submitting the job")
    provider = self.w3.toChecksumAddress(provider)
    if not env.IS_BLOXBERG:
        if account_id and not requester:
            _from = self.w3.toChecksumAddress(self.w3.eth.accounts[account_id])
        else:
            _from = self.w3.toChecksumAddress(requester)
    else:
        _from = requester

    try:
        provider_info = self.get_provider_info(provider)
        log(f"Provider's available_core_num={provider_info['available_core_num']}")
        log(f"Provider's price_core_min={provider_info['price_core_min']}")
    except Exception as e:
        print_tb(e)
        raise e

    self.check_before_submit(provider, _from, provider_info, key, job)
    provider_price_block_number = self._get_provider_set_block_numbers(provider)
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
        # source_code_hashes_l = []
        # for idx, source_code_hash in job.source_code_hashes:
        #     source_code_hashes_l.append(bytes32_to_ipfs(source_code_hash))
        # log(f"==> source_code_hashes={source_code_hashes_l}")
        tx = self._submit_job(
            _from, job_price, key, job.data_transfer_ins, args, job.storage_hours, job.source_code_hashes
        )
        return self.tx_id(tx)
    except TransactionError as e:
        log(f"Warning: {e}")
        tx_hash = str(e).replace("Tx dropped without known replacement: ", "")
        if is_transaction_valid(tx_hash):
            return tx_hash
        else:
            raise Exception(f"E: tx_hash={tx_hash} is not a valid transaction hash.")
    except Exception as e:
        if "authentication needed: password or unlock" in getattr(e, "message", repr(e)):
            # https://stackoverflow.com/a/45532289/2402577, https://stackoverflow.com/a/24065533/2402577
            raise config.QuietExit

        raise e
