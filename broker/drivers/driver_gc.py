#!/usr/bin/env python3

from pymongo import MongoClient

from broker import cfg
from broker.config import env
from broker.utils import StorageID, _remove, run

Ebb = cfg.Ebb
cl = MongoClient()
coll = cl["eBlocBroker"]["cache"]


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
            print(run(["ipfs", "pin", "rm", ipfsHash]))
            print(run(["ipfs", "repo", "gc"]))
        else:
            cachedFileName = (
                env.PROGRAM_PATH + "/" + document["requesterID"] + "/cache/" + document["sourceCodeHash"] + "tar.gz"
            )
            print(cachedFileName)
            _remove(cachedFileName)
            cachedFileName = env.PROGRAM_PATH + "/cache/" + document["sourceCodeHash"] + "tar.gz"
            print(cachedFileName)
            _remove(cachedFileName)

        print(received_block_number)
        output = coll.delete_one({"jobKey": ipfsHash})
