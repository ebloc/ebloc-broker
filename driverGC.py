#!/usr/bin/env python3

from contractCalls.get_block_number import get_block_number
from contractCalls.getJobStorageTime import getJobStorageTime
from imports import connect
from lib import StorageID, run_command, silent_remove
from pymongo import MongoClient

from settings import init_env

env = init_env()

cl = MongoClient()
coll = cl["eBlocBroker"]["cache"]

eBlocBroker, w3 = connect()

"""find_all"""
block_number = get_block_number()
print(block_number)

storageID = None
cursor = coll.find({})
for document in cursor:
    # print(document)
    received_block_number, storage_time = getJobStorageTime(env.PROVIDER_ID, document["sourceCodeHash"])
    endBlockTime = received_block_number + storage_time * 240
    storageID = document["storageID"]
    if endBlockTime < block_number and received_block_number != 0:
        if storageID == StorageID.IPFS or storageID == StorageID.IPFS_MINILOCK:
            ipfsHash = document["jobKey"]
            cmd = ["ipfs", "pin", "rm", ipfsHash]
            success, output = run_command(cmd)
            print(output)
            success, output = run_command(["ipfs", "repo", "gc"])
            print(output)
        else:
            cachedFileName = env.PROGRAM_PATH + "/" + document["requesterID"] + "/cache/" + document["sourceCodeHash"] + "tar.gz"
            print(cachedFileName)
            silent_remove(cachedFileName)
            cachedFileName = env.PROGRAM_PATH + "/cache/" + document["sourceCodeHash"] + "tar.gz"
            print(cachedFileName)
            silent_remove(cachedFileName)

        print(received_block_number)
        output = coll.delete_one({"jobKey": ipfsHash})
