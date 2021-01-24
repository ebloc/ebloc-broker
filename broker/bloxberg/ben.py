#!/usr/bin/env python3

import os
import sys
from pprint import pprint

from web3.logs import DISCARD

import broker.eblocbroker.Contract as Contract
from broker.config import QuietExit, env, logging
from broker.lib import check_linked_data, get_tx_status, run
from broker.libs import ipfs
from broker.libs.ipfs import gpg_encrypt
from broker.utils import (
    CacheType,
    StorageID,
    _colorize_traceback,
    generate_md5sum,
    ipfs_to_bytes32,
    is_bin_installed,
    is_dpkg_installed,
    log,
    silent_remove,
)
from brownie import accounts, network, project, web3
from contract.scripts.lib import Job, cost

#!/usr/bin/env python3


def pre_check():
    """Pre check jobs to submit."""
    try:
        is_bin_installed("ipfs")
        if not is_dpkg_installed("pigz"):
            log("E: Install pigz:\nsudo apt-get install -y pigz")
            sys.exit()
    except Exception as e:
        print(str(e))
        sys.exit()


def get_tx_status(tx_hash) -> str:
    print(f"tx_hash={tx_hash}")
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    print("Transaction receipt is mined:")
    pprint(dict(tx_receipt), depth=1)
    print("\n## Was transaction successful? ")
    if tx_receipt["status"] == 1:
        print("Transaction is deployed", color="green")
    else:
        raise Exception("E: Transaction is reverted")
    return tx_receipt


if __name__ == "__main__":
    Ebb = Contract.eblocbroker = Contract.Contract()
    job = Job()
    pre_check()

    # network.connect("bloxberg")
    # project = project.load("/mnt/hgfs/ebloc-broker/contract")
    # ebb = project.eBlocBroker.at("0xccD25f5Ae21037a6DCCff829B01034E2fD332796")
    # print(ebb.getOwner())
    #
    ops = {"from": "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49", "value": web3.toWei(105, "wei"), "gas_limit": 300000}
    key = "QmYc9Zmuv1w2VGkmyTqpSSv3R8PtBkjM5sdnF27i6PKDwg"
    data_transfer_ins = [1, 1]
    args = ["0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49", 11282972, [2, 2], [1, 1], [0, 0], [1], [1], 1]

    storage_hours = [1, 1]
    source_code_hashes = [
        b"\x98\x8d5\x9a ?\xad\xe1M\x83.d'u\xbb8\xb3\xbe_\xe2\xd3W\x85iHs\x9b\xff5\xa8\xac\xa3",
        b"x<V}:\x8d\xbfOf\x89k\x16\x17\xab\x1d\xefe\xbaz\x06\x0bTu^\xaf\xc4q`:\x99\x06;",
    ]

    accounts.load(filename="alper.json", password="alper")
    # tx_hash = ebb.submitJob(key, data_transfer_ins, args, storage_hours, source_code_hashes, ops)
    Ebb.foo()
    tx_hash = Ebb._submit_job(
        "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49",
        105,
        key,
        data_transfer_ins,
        args,
        storage_hours,
        source_code_hashes,
    )

    print(tx_hash.txid)
    receipt = get_tx_status(tx_hash.txid)
