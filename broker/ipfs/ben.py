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
    log("==> Attemptting to submit a job")
    Ebb = Contract.eblocbroker = Contract.Contract()
    job = Job()
    pre_check()

    provider = Ebb.w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")
    requester_addr = Ebb.w3.toChecksumAddress("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49")
    try:
        job.check_account_status(requester_addr)
    except Exception as e:
        _colorize_traceback(e)

    # job.storage_ids = [StorageID.IPFS, StorageID.IPFS]
    # job.storage_ids = [StorageID.IPFS_GPG, StorageID.IPFS]
    job.storage_ids = [StorageID.IPFS_GPG, StorageID.IPFS_GPG]
    _types = [CacheType.PUBLIC, CacheType.PUBLIC]

    main_storage_id = job.storage_ids[0]
    job.set_cache_types(_types)

    # TODO: let user directly provide the IPFS hash instead of the folder
    folders = []  # full paths are provided
    folders.append(f"{env.BASE_DATA_PATH}/test_data/base/source_code")
    folders.append(f"{env.BASE_DATA_PATH}/test_data/base/data/data1")

    path_from = f"{env.EBLOCPATH}/base/data"
    path_to = f"{env.LINKS}/base/data_link"
    check_linked_data(path_from, path_to, folders[1:])
    for folder in folders:
        if not os.path.isdir(folder):
            log(f"E: {folder} path does not exist")
            sys.exit(1)

    if main_storage_id == StorageID.IPFS:
        log("==> Submitting source code through IPFS")
    elif main_storage_id == StorageID.IPFS_GPG:
        log("==> Submitting source code through IPFS_GPG")
    else:
        log("E: Please provide IPFS or IPFS_GPG storage type")
        sys.exit(1)

    targets = []
    for idx, folder in enumerate(folders):
        try:
            provider_info = Ebb.get_provider_info(provider)
        except:
            sys.exit()

        target = folder
        if job.storage_ids[idx] == StorageID.IPFS_GPG:
            provider_gpg_finderprint = "11FBA2D03D3CFED18FC71D033B127BC747AADC1C"  # provider_info["gpg_fingerprint"]
            if not provider_gpg_finderprint:
                log("E: Provider did not register any GPG fingerprint")
                sys.exit(1)

            try:
                # target is updated
                target = gpg_encrypt(provider_gpg_finderprint, target)
                log(f"==> GPG_file={target}")
            except:
                sys.exit(1)

        try:
            ipfs_hash = ipfs.add(target)
            # ipfs_hash = ipfs.add(folder, True)  # True includes .git/
            run(["ipfs", "refs", ipfs_hash])  # TODO use ipfs python
        except:
            _colorize_traceback()
            sys.exit(1)

        if idx == 0:
            key = ipfs_hash

        job.source_code_hashes.append(ipfs_to_bytes32(ipfs_hash))
        log(f"==> ipfs_hash: {ipfs_hash}\nmd5sum: {generate_md5sum(target)}", color="yellow")
        if main_storage_id == StorageID.IPFS_GPG:
            # created .gpg file will be removed since its already in ipfs
            targets.append(target)

        if idx != len(folders) - 1:
            log("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-", color="cyan")

    # Requester inputs for testing purpose
    job.cores = [1]
    job.run_time = [1]
    job.storage_hours = [1, 1]
    job.data_transfer_ins = [1, 1]  # TODO: calculate from the file itself
    job.dataTransferOut = 1
    job.data_prices_set_block_numbers = [0, 0]
    job_price, _cost = cost(provider, requester_addr, job)  # <============

    try:
        tx_hash = Ebb.submit_job(provider, key, 105, job, requester=requester_addr)
        tx_receipt = get_tx_status(tx_hash)
        if tx_receipt["status"] == 1:
            processed_logs = Ebb.eBlocBroker.events.LogJob().processReceipt(tx_receipt, errors=DISCARD)
            pprint(vars(processed_logs[0].args))
            try:
                log(f"job_index={processed_logs[0].args['index']}")
                log("SUCCESS")
                for target in targets:
                    silent_remove(target)
            except IndexError:
                logging.error("E: Transaction is reverted")
    except QuietExit:
        sys.exit(1)
    except Exception as e:
        _colorize_traceback(e)
        sys.exit(1)
    finally:
        pass

    # # try:
    # #     job.check_account_status(requester_addr)
    # # except Exception as e:
    # #     _colorize_traceback(e)
    # #     raise e

    # # network.connect("bloxberg")
    # # project = project.load("/mnt/hgfs/ebloc-broker/contract")
    # # ebb = project.eBlocBroker.at("0xccD25f5Ae21037a6DCCff829B01034E2fD332796")
    # # print(ebb.getOwner())
    # #
    # ops = {"from": requester_addr, "value": web3.toWei(105, "wei"), "gas_limit": 300000}
    # key = "QmYc9Zmuv1w2VGkmyTqpSSv3R8PtBkjM5sdnF27i6PKDwg"
    # data_transfer_ins = [1,1]
    # args = [provider,
    #  11282972,
    #  [2, 2],
    #  [1, 1],
    #  [0, 0],
    #  [1],
    #  [1],
    #  1]

    # storage_hours = [1, 1]
    # source_code_hashes = [b"\x98\x8d5\x9a ?\xad\xe1M\x83.d'u\xbb8\xb3\xbe_\xe2\xd3W\x85iHs\x9b\xff5\xa8\xac\xa3", b'x<V}:\x8d\xbfOf\x89k\x16\x17\xab\x1d\xefe\xbaz\x06\x0bTu^\xaf\xc4q`:\x99\x06;']

    # accounts.load(filename="alper.json", password="alper")
    # # tx_hash = ebb.submitJob(key, data_transfer_ins, args, storage_hours, source_code_hashes, ops)
    # Ebb.foo()
    # tx_hash = Ebb._submit_job("0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49", 105, key, data_transfer_ins, args, storage_hours, source_code_hashes)

    # print(tx_hash.txid)
    # receipt = get_tx_status(tx_hash.txid)
