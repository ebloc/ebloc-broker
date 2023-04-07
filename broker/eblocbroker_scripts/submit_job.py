#!/usr/bin/env python3

from broker import cfg
from broker._utils._log import br
from broker._utils.tools import log, print_tb
from broker.eblocbroker_scripts.job import Job
from broker.eblocbroker_scripts.utils import Cent
from broker.errors import QuietExit
from broker.utils import StorageID, is_ipfs_on, question_yes_no
from brownie.exceptions import TransactionError

Ebb = cfg.Ebb
ipfs = cfg.ipfs


def is_provider_valid(self, provider):
    provider = self.w3.toChecksumAddress(provider)
    if not self.does_provider_exist(provider):
        raise ValueError(f"Requested provider's Ethereum address {provider} does not registered")


def is_requester_valid(self, _from):
    _from = self.w3.toChecksumAddress(_from)
    *_, orcid = self._get_requester_info(_from)
    if not self.does_requester_exist(_from):
        raise Exception(f"Requester's Ethereum address {_from} is not registered")

    if not self._is_orc_id_verified(_from):
        if orcid:
            raise Exception(f"Requester({_from})'s orcid: {orcid.decode('UTF')} is not verified")

        raise Exception(f"Requester({_from})'s orcid is not registered")


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

    if not job.code_hashes:
        raise Exception("source_code_hash list is empty")

    if len(key) >= 64:
        raise Exception("Length of key is greater than 64, please provide lesser")

    len_key = 46
    if len(key) != len_key and main_storage_id in [StorageID.IPFS, StorageID.IPFS_GPG]:
        raise Exception(
            f"key's length does not match with its original length, it should be {len_key}. "
            f"Please check your key length, given key={key}"
        )

    len_key = 33
    if len(key) != 33 and main_storage_id == StorageID.GDRIVE:
        raise Exception(
            f"key's length does not match with its original length, it should be {len_key}. "
            "Please check your key length"
        )

    for idx, core in enumerate(job.cores):
        if core > provider_info["available_core_num"]:
            raise Exception(f"Requested {core}, which is {core}, is greater than the provider's core number")

        if job.run_time[idx] == 0:
            raise Exception(f"run_time{br(idx)} is provided as 0. Please provide non-zero value")

    for core_min in job.run_time:
        if core_min > 14400:
            raise Exception("run_time provided greater than 14400. Please provide smaller value")

    for cache_type in job.cache_types:
        if cache_type > 1:
            raise Exception(
                f"cache_type ({cache_type}) provided greater than 1,"
                "where it should be `0: PUBLIC` or `1: PRIVATE`. Please provide smaller value"
            )

    if is_use_ipfs:
        if not is_ipfs_on():
            raise Exception("ipfs daemon is not running in the background")

        try:
            ipfs.swarm_connect(provider_info["ipfs_address"])
        except Exception as e:
            log(f"E: {e}")
            if not cfg.IS_FULL_TEST and not question_yes_no("#> Would you like to continue?"):
                raise QuietExit from e

    for idx, source_code_hash in enumerate(job.code_hashes_str):
        if source_code_hash == "":
            raise Exception(f"source_code_hash{br(idx)} should not be empty string")

    if job.price == 0:
        raise Exception("E: job.price is 0 ; something is wrong")

    balance = self.get_balance(job.requester)
    if job.price > Cent(balance):
        raise Exception(f"E: Calculated job_price={job.price} is greater than requester's balance={Cent(balance)}")


def submit_job(self, provider, key, job: Job, requester=None, required_confs=1, is_verbose=False):
    """Submit job.

    - How to properly get exception messages in Python:
    __ https://stackoverflow.com/a/45532289/2402577
    __ https://stackoverflow.com/a/24065533/2402577
    """
    if not provider and not requester:
        raise Exception("Not valid msg.sender address is provided.")

    provider = self.w3.toChecksumAddress(provider)
    _from = self.w3.toChecksumAddress(requester)
    log(f"==> Submitting the job({job.code_hashes_str[0]})")
    try:
        provider_info = self.get_provider_info(provider)
        if is_verbose:
            log(f"provider's available_core_num={provider_info['available_core_num']}")
            log(f"provider's price_core_min={Cent(provider_info['price_core_min'])._to()} [blue]usd")
    except Exception as e:
        print_tb(e)
        raise e

    self.check_before_submit(provider, _from, provider_info, key, job)
    args = [
        provider,
        self._get_provider_set_block_numbers(provider),
        job.storage_ids,
        job.cache_types,
        job.data_prices_set_block_numbers,
        job.cores,
        job.run_time,
        job.data_transfer_out,
        job.price,
    ]
    job.print_before_submit()
    try:
        # code_hashes_l = []
        # for idx, source_code_hash in job.code_hashes:
        #     code_hashes_l.append(bytes32_to_ipfs(source_code_hash))
        # log(f"==> code_hashes={code_hashes_l}")
        tx = self._submit_job(
            required_confs,
            _from,
            job.price,
            key,
            job.data_transfer_ins,
            args,
            job.storage_hours,
            job.code_hashes,
        )
        return self.tx_id(tx)
    except TransactionError as e:
        log(f"warning: {e}")
        tx_hash = str(e).replace("Tx dropped without known replacement: ", "")
        if Ebb.is_transaction_valid(tx_hash):
            return tx_hash
        else:
            raise Exception(f"tx_hash={tx_hash} is not a valid transaction hash.") from e
    except Exception as e:
        if "authentication needed: password or unlock" in getattr(e, "message", repr(e)):
            raise QuietExit from None

        raise e  # "No valid Tx receipt is generated"
