#!/usr/bin/env python3

from pymongo import MongoClient

import lib
import lib_mongodb
from contractCalls.blockNumber import blockNumber
from contractCalls.getJobStorageTime import getJobStorageTime
from imports import connect_to_eblocbroker, connect_to_web3
from lib import silentremove

cl = MongoClient()
coll = cl["eBlocBroker"]["cache"]


web3 = connect_to_web3()
eBlocBroker = connect_to_eblocbroker()

"""find_all"""
blockNum = int(blockNumber())
print(str(blockNum))

storageID = None
cursor = coll.find({})
for document in cursor:
    # print(document)
    receivedBlockNum, storageTime = getJobStorageTime(lib.PROVIDER_ID, document["sourceCodeHash"])
    endBlockTime = receivedBlockNum + storageTime * 240
    storageID = document["storageID"]
    if endBlockTime < blockNum and receivedBlockNum != 0:
        if storageID == lib.StorageID.IPFS or storageID == lib.StorageID.IPFS_MINILOCK:
            ipfsHash = document["jobKey"]
            command = ["ipfs", "pin", "rm", ipfsHash]
            status, res = lib.execute_shell_command(command)
            print(res)
            status, res = lib.execute_shell_command(["ipfs", "repo", "gc"])
            print(res)
        else:
            cachedFileName = (
                lib.PROGRAM_PATH + "/" + document["requesterID"] + "/cache/" + document["sourceCodeHash"] + "tar.gz"
            )
            print(cachedFileName)
            silentremove(cachedFileName)
            cachedFileName = lib.PROGRAM_PATH + "/cache/" + document["sourceCodeHash"] + "tar.gz"
            print(cachedFileName)
            silentremove(cachedFileName)

        print(receivedBlockNum)
        result = coll.delete_one({"jobKey": ipfsHash})
