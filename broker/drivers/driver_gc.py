#!/usr/bin/env python3

from pymongo import MongoClient

from broker import cfg
from broker._utils.tools import _remove
from broker.config import env
from broker.utils import StorageID, run

Ebb = cfg.Ebb
cl = MongoClient()


def main():
    coll = cl["eBlocBroker"]["cache"]
    block_number = Ebb.get_block_number()
    storageID = None
    cursor = coll.find({})
    for document in cursor:
        # print(document)
        # TODO: requester paramer as get_storage_duration
        received_bn, storage_duration = Ebb.get_job_storage_duration(env.PROVIDER_ID, document["sourceCodeHash"])
        end_block_time = received_bn + storage_duration * cfg.ONE_HOUR_BLOCK_DURATION
        storageID = document["storageID"]
        if end_block_time < block_number and received_bn != 0:
            if storageID in (StorageID.IPFS, StorageID.IPFS_GPG):
                ipfsHash = document["jobKey"]
                print(run(["ipfs", "pin", "rm", ipfsHash]))
                print(run(["ipfs", "repo", "gc"]))
            else:
                cached_file_name = (
                    env.PROGRAM_PATH / document["requesterID"] / "cache" / document["sourceCodeHash"] + "tar.gz"
                )
                print(cached_file_name)
                _remove(cached_file_name)
                cached_file_name = env.PROGRAM_PATH / "cache" / document["sourceCodeHash"] + "tar.gz"
                print(cached_file_name)
                _remove(cached_file_name)

            print(received_bn)
            coll.delete_one({"jobKey": ipfsHash})


if __name__ == "__main__":
    main()
