#!/usr/bin/env python3


import subprocess
import sys
import time

import libs.eudat as eudat
import owncloud
from imports import connect
from utils import generate_md5sum, print_tb

import broker.eblocbroker.Contract as Contract

oc = owncloud.Client("https://b2drop.eudat.eu/")
oc.login("059ab6ba-4030-48bb-b81b-12115f531296", "qPzE2-An4Dz-zdLeK-7Cx4w-iKJm9")
Ebb: "Contract.Contract" = Contract.EBB()


def eudatSubmitJob(tar_hash=None):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return False, "web3 is not connected"

    provider = "0x4e4a0750350796164D8DefC442a712B7557BF282"
    providerAddress = w3.toChecksumAddress(provider)

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
    jobDescription = "science"
    cloudStorageID = 1
    account_id = 0

    try:
        tx_hash = Ebb.submit_job(
            str(provider),
            str(tar_hash),
            coreNum,
            coreMinuteGas,
            str(jobDescription),
            cloudStorageID,
            str(tar_hash),
            account_id,
        )
        print(tx_hash)
    except:
        print_tb()
        sys.exit(1)


if __name__ == " __main__":
    if len(sys.argv) == 2:
        print("Provided hash=" + sys.argv[1])  # tar_hash = '656e8fca04058356f180ae4ff26c33a8'
        success, output = eudatSubmitJob(sys.argv[1])
    else:
        success, output = eudatSubmitJob()
