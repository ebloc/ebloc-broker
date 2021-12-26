#!/usr/bin/env python3

import sys

from broker import cfg
from broker._utils._log import br
from broker._utils.tools import get_gpg_fingerprint, is_gpg_published, log, print_tb
from broker.config import env
from broker.errors import QuietExit
from broker.lib import run
from broker.utils import StorageID, is_ipfs_on, is_transaction_valid, question_yes_no
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
            raise Exception("Wrong storage_ids value is given. Please provide from 0 to 4")

        if storage_id in [StorageID.IPFS, StorageID.IPFS_GPG]:
            is_use_ipfs = True
            break

    if not job.source_code_hashes:
        raise Exception("source_code_hash list is empty")

    if len(key) >= 64:
        raise Exception("Length of key is greater than 64, please provide lesser")

    key_len = 46
    if len(key) != key_len and main_storage_id in [StorageID.IPFS, StorageID.IPFS_GPG]:
        raise Exception(
            f"E: key's length does not match with its original length, it should be {key_len}. "
            f"Please check your key length, given key={key}"
        )

    key_len = 33
    if len(key) != 33 and main_storage_id == StorageID.GDRIVE:
        raise Exception(
            f"E: key's length does not match with its original length, it should be {key_len}. "
            "Please check your key length"
        )

    for idx, core in enumerate(job.cores):
        if core > provider_info["available_core_num"]:
            raise Exception(f"Requested {core}, which is {core}, is greater than the provider's core number")

        if job.run_time[idx] == 0:
            raise Exception(f"run_time{br(idx)} is provided as 0. Please provide non-zero value")

    for core_min in job.run_time:
        if core_min > 1440:
            raise Exception("E: run_time provided greater than 1440. Please provide smaller value")

    for cache_type in job.cache_types:
        if cache_type > 1:
            # cache_type = {0: private, 1: public}
            raise Exception(f"E: cache_type ({cache_type}) provided greater than 1. Please provide smaller value")

    if is_use_ipfs:
        if not is_ipfs_on():
            sys.exit()

        try:
            cfg.ipfs.swarm_connect(provider_info["ipfs_id"])
        except Exception as e:
            log(f"E: {e}")
            if not question_yes_no("#> Would you like to continue?"):
                raise QuietExit from e

    for idx, source_code_hash in enumerate(job.source_code_hashes_str):
        if source_code_hash == "":
            raise Exception(f"source_code_hash{br(idx)} should not be empty string")

    requester_info = self.get_requester_info(_from)
    gpg_fingerprint = get_gpg_fingerprint(env.GMAIL).upper()
    if requester_info["gpg_fingerprint"].upper() != gpg_fingerprint:
        raise Exception(
            f"E: gpg_fingerprint does not match {requester_info['gpg_fingerprint'].upper()} "
            f"with registered gpg_fingerprint={gpg_fingerprint}"
        )

    try:
        is_gpg_published(gpg_fingerprint)
    except Exception as e:
        raise e


def submit_job(self, provider, key, job, requester=None, account_id=None, required_confs=1):
    """Submit job.

    How to get exception message in Python properly:
    __ https://stackoverflow.com/a/45532289/2402577
    __ https://stackoverflow.com/a/24065533/2402577
    """
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
        log(f"Provider's available_core_num={provider_info['available_core_num']}", "bold")
        log(f"Provider's price_core_min={provider_info['price_core_min']}", "bold")
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
        job.data_transfer_out,
    ]
    job.print_before_submit()
    try:
        # source_code_hashes_l = []
        # for idx, source_code_hash in job.source_code_hashes:
        #     source_code_hashes_l.append(bytes32_to_ipfs(source_code_hash))
        # log(f"==> source_code_hashes={source_code_hashes_l}")
        tx = self._submit_job(
            required_confs,
            _from,
            job.price,
            key,
            job.data_transfer_ins,
            args,
            job.storage_hours,
            job.source_code_hashes,
        )
        return self.tx_id(tx)
    except TransactionError as e:
        log(f"Warning: {e}")
        tx_hash = str(e).replace("Tx dropped without known replacement: ", "")
        if is_transaction_valid(tx_hash):
            return tx_hash
        else:
            raise Exception(f"E: tx_hash={tx_hash} is not a valid transaction hash.") from e
    except Exception as e:
        if "authentication needed: password or unlock" in getattr(e, "message", repr(e)):
            raise QuietExit  # noqa

        raise e
