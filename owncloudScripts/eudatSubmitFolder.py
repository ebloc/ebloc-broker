#!/usr/bin/env python3

import os
import subprocess
import sys
import time

import owncloud

import lib
from contractCalls.submitJob import submitJob
from imports import connect
from lib_owncloud import isOcMounted, singleFolderShare

oc = owncloud.Client("https://b2drop.eudat.eu/")
oc.login("059ab6ba-4030-48bb-b81b-12115f531296", "qPzE2-An4Dz-zdLeK-7Cx4w-iKJm9")


def eudatSubmitJob(tarHash=None, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect()
    if eBlocBroker is None or w3 is None:
        return False, "web3 is not connected"

    provider = "0x4e4a0750350796164D8DefC442a712B7557BF282"
    providerAddress = w3.toChecksumAddress(provider)

    blockReadFrom, availableCoreNum, priceCoreMin, priceDataTransfer, priceStorage, priceCache = eBlocBroker.functions.getProviderInfo(
        providerAddress
    ).call()
    my_filter = eBlocBroker.eventFilter(
        "LogProvider", {"fromBlock": int(blockReadFrom), "toBlock": int(blockReadFrom) + 1}
    )
    fID = my_filter.get_all_entries()[0].args["fID"]

    if tarHash is None:
        folderToShare = "exampleFolderToShare"
        subprocess.run(["sudo", "chmod", "-R", "777", folderToShare])
        tarHash = subprocess.check_output(["../scripts/generateMD5sum.sh", folderToShare]).decode("utf-8").strip()
        tarHash = tarHash.split(" ", 1)[0]
        print("hash=" + tarHash)
        subprocess.run(["rm", "-rf", tarHash])
        subprocess.run(["cp", "-a", folderToShare + "/", tarHash])
        res = oc.put_directory("./", tarHash)
        if not res:
            sys.exit()

    time.sleep(1)
    print(singleFolderShare(tarHash, oc, fID))
    # subprocess.run(['python', 'singleFolderShare.py', tarHash])
    print("\nSubmitting Job...")
    coreNum = 1
    coreMinuteGas = 5
    jobDescription = "science"
    cloudStorageID = 1
    accountID = 0

    res = submitJob(
        str(provider),
        str(tarHash),
        coreNum,
        coreMinuteGas,
        str(jobDescription),
        cloudStorageID,
        str(tarHash),
        accountID,
    )
    print(res)


if __name__ == "__main__":
    if len(sys.argv) == 2:
        print("Provided hash=" + sys.argv[1])  # tarHash = '656e8fca04058356f180ae4ff26c33a8'
        status, result = eudatSubmitJob(sys.argv[1])
    else:
        status, result = eudatSubmitJob()
