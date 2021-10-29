#!/usr/bin/env python3


import subprocess
import sys
import time

import owncloud

import broker.cfg as cfg
import broker.libs.eudat as eudat
from broker.imports import connect
from broker.utils import generate_md5sum, print_tb

oc = owncloud.Client("https://b2drop.eudat.eu/")
oc.login("059ab6ba-4030-48bb-b81b-12115f531296", "qPzE2-An4Dz-zdLeK-7Cx4w-iKJm9")
Ebb = cfg.Ebb


def eudat_submit_job(tar_hash=None):
    provider = "0x4e4a0750350796164D8DefC442a712B7557BF282"
    providerAddress = Ebb.w3.toChecksumAddress(provider)

    (
        blockReadFrom,
        availableCoreNum,
        price_core_min,
        price_data_transfer,
        price_storage,
        price_cache,
    ) = eBlocBroker.functions.getProviderInfo(providerAddress).call()
    my_filter = eBlocBroker.eventFilter(
        "LogProvider",
        {"fromBlock": int(blockReadFrom), "toBlock": int(blockReadFrom) + 1},
    )
    fID = my_filter.get_all_entries()[0].args["fID"]

    if tar_hash is None:
        folderToShare = "exampleFolderToShare"
        subprocess.run(["sudo", "chmod", "-R", "777", folderToShare])
        tar_hash = generate_md5sum(folderToShare)
        tar_hash = tar_hash.split(" ", 1)[0]
        print("hash=" + tar_hash)
        subprocess.run(["rm", "-rf", tar_hash])
        subprocess.run(["cp", "-a", folderToShare + "/", tar_hash])
        output = oc.put_directory("./", tar_hash)
        if not output:
            sys.exit(1)

    time.sleep(1)
    print(eudat.share_single_folder(tar_hash, oc, fID))
    # subprocess.run(['python', 'eudat.share_single_folder.py', tar_hash])
    print("\nSubmitting Job...")
    coreNum = 1
    coreMinuteGas = 5
    cloudStorageID = 1
    account_id = 0
    try:
        tx_hash = Ebb.submit_job(
            str(provider),
            str(tar_hash),
            coreNum,
            coreMinuteGas,
            cloudStorageID,
            str(tar_hash),
            account_id,
        )
        print(tx_hash)
    except Exception as e:
        print_tb(e)
        sys.exit(1)


if __name__ == " __main__":
    if len(sys.argv) == 2:
        print("Provided hash=" + sys.argv[1])  # tar_hash = '656e8fca04058356f180ae4ff26c33a8'
        eudat_submit_job(sys.argv[1])
    else:
        eudat_submit_job()
