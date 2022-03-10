#!/usr/bin/env python3

from broker import cfg
from broker._utils._log import br, log
from broker._utils.tools import print_tb
from broker._utils.web3_tools import get_tx_status
from broker.errors import QuietExit
from broker.utils import StorageID, bytes32_to_ipfs

# TODO: list all jobs and fetch there datasets
Ebb = cfg.Ebb


def deposit_storage(eth_address, is_provider=False):
    """Deposit storage balance.

    :param str eth_address: Ethereum address of the provider
    :param bool is_provider: Checks it the caller provider
    """
    from_block = Ebb.get_deployed_block_number()
    if is_provider:
        event_filter = Ebb._eBlocBroker.events.LogJob.createFilter(
            fromBlock=int(from_block),
            argument_filters={"provider": eth_address},
            toBlock="latest",
        )
    else:  # should be owner of the job
        event_filter = Ebb._eBlocBroker.events.LogJob.createFilter(
            fromBlock=int(from_block),
            argument_filters={"owner": eth_address},
            toBlock="latest",
        )

    for job in enumerate(event_filter.get_all_entries()):
        job_info = job[1].args
        # job_provider = job_info["provider"]
        for idx, code_hash in enumerate(job_info["sourceCodeHash"]):
            main_cloud_storage_id = job_info["cloudStorageID"][idx]
            if main_cloud_storage_id in (StorageID.IPFS, StorageID.IPFS_GPG):
                _hash = bytes32_to_ipfs(code_hash)
                _type = "ipfs_hash"
            else:
                _hash = cfg.w3.toText(code_hash)
                _type = "md5sum"

            log(br(f"{idx}, {_type}"), "bold cyan", end="")
            if len(code_hash) <= 32:
                log(f" {_hash} bytes={code_hash}", "bold")
            else:
                log(f" {_hash}\n\t{code_hash}", "bold")

            provider = Ebb.w3.toChecksumAddress(job_info["provider"])
            if is_provider and eth_address.lower() == provider.lower():
                data_owner = Ebb.w3.toChecksumAddress(job_info["owner"])
                deposit = Ebb.get_received_storage_deposit(provider, data_owner, code_hash)
                if deposit > 0:
                    print(deposit)
                    tx = Ebb.deposit_storage(data_owner, code_hash, eth_address)
                    get_tx_status(Ebb.tx_id(tx))


if __name__ == "__main__":
    try:
        deposit_storage("0x3e6ffc5ede9ee6d782303b2dc5f13afeee277aea", is_provider=True)
    except QuietExit:
        pass
    except Exception:
        breakpoint()  # DEBUG
