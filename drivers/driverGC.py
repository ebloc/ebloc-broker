#!/usr/bin/env python3

from pymongo import MongoClient

import eblocbroker.Contract as Contract
from config import env
from imports import connect
from lib import run_command, silent_remove
from utils import StorageID

cl = MongoClient()
coll = cl["eBlocBroker"]["cache"]

eBlocBroker, w3 = connect()
Ebb = Contract.eblocbroker

"""find_all"""
block_number = Ebb.get_block_number()
print(block_number)

storageID = None
cursor = coll.find({})
for document in cursor:
    # print(document)
    received_block_number, storage_time = Ebb.get_job_storage_time(env.PROVIDER_ID, document["sourceCodeHash"])
    endBlockTime = received_block_number + storage_time * 240
    storageID = document["storageID"]
    if endBlockTime < block_number and received_block_number != 0:
        if storageID in (StorageID.IPFS, StorageID.IPFS_GPG):
            ipfsHash = document["jobKey"]
            cmd = ["ipfs", "pin", "rm", ipfsHash]
            success, output = run_command(cmd)
            print(output)
            success, output = run_command(["ipfs", "repo", "gc"])
            print(output)
        else:
            cachedFileName = (
                env.PROGRAM_PATH + "/" + document["requesterID"] + "/cache/" + document["sourceCodeHash"] + "tar.gz"
            )
            print(cachedFileName)
            silent_remove(cachedFileName)
            cachedFileName = env.PROGRAM_PATH + "/cache/" + document["sourceCodeHash"] + "tar.gz"
            print(cachedFileName)
            silent_remove(cachedFileName)

        print(received_block_number)
        output = coll.delete_one({"jobKey": ipfsHash})
