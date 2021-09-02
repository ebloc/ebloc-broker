#!/usr/bin/env python3

import argparse
from pprint import pprint

from pymongo import MongoClient


class BaseMongoClass:
    def __init__(self, mc, collection) -> None:
        self.mc = mc
        self.collection = collection

    def delete_all(self):
        return self.collection.delete_many({}).acknowledged

    def find_key(self, key, _key):
        output = self.collection.find_one({key: _key})
        if bool(output):
            return output
        else:
            raise Exception("E: Coudn't find key")

    def find_all(self):
        """find_all"""
        cursor = self.collection.find({})
        for document in cursor:
            pprint(document)
        # coll = mc["ebloc_broker"]["shareID"]
        # print(document['_id'])
        # print(document['timestamp'])


class MongoBroker(BaseMongoClass):
    def __init__(self, mc, collection) -> None:
        super().__init__(mc, collection)

    def add_item(self, job_key, index, source_code_hash_list, requester_id, timestamp, cloudStorageID, job_info):
        """Adding job_key info along with its cache_duration into mongoDB."""
        item = {
            "requester_address": job_info["job_owner"],
            "requester_id": requester_id,
            "job_key": job_key,
            "index": index,
            "source_code_hash": source_code_hash_list,
            "received_block_number": job_info["received_block_number"],
            "timestamp": timestamp,
            "cloudStorageID": cloudStorageID,
            "cacheDuration": job_info["cacheDuration"],
            "receieved": False,
        }
        res = self.collection.replace_one({"job_key": item["job_key"]}, item, True)
        return res.acknowledged

    def delete_one(self, job_key):
        res = self.collection.delete_one({"job_key": job_key})
        return res.acknowledged

    def add_item_share_id(self, key, shareID, share_token):
        coll = self.mc["ebloc_broker"]["shareID"]
        item = {"job_key": key, "shareID": shareID, "share_token": share_token}
        res = coll.update({"job_key": item["job_key"]}, item, True)
        return res.acknowledged

    def find_key(self, _coll, key):
        output = _coll.find_one({"job_key": key})
        if bool(output):
            return output
        else:
            raise

    def get_job_block_number(self, requester_address, key, index) -> int:
        cursor = self.collection.find({"requester_address": requester_address.lower(), "job_key": key, "index": index})
        for document in cursor:
            return document["received_block_number"]
        else:
            return 0

    def is_received(self, requester_address, key, index, is_print=False) -> bool:
        cursor = self.collection.find({"requester_address": requester_address.lower(), "job_key": key, "index": index})
        if is_print:
            for document in cursor:
                pprint(document)

        if cursor.count() == 0:
            return False
        return True


if __name__ == "__main__":
    mc = MongoClient()
    mongo = MongoBroker(mc, mc["ebloc_broker"]["cache"])
    #
    parser = argparse.ArgumentParser(description="Process MongoDB.")
    parser.add_argument("--delete-all", dest="is_delete_all", action="store_true", help="Clean job [cache]")
    parser.add_argument("--no-delete-all", dest="is_delete_all", action="store_false")
    #: It's very useful in scripting these CLIs to have the flexibility to
    # declare exactly what behavior you want (then you aren't subject to the
    # whims of anyone who decides to change the default).
    # __ https://stackoverflow.com/a/15008806/2402577
    parser.set_defaults(is_delete=False)
    args = parser.parse_args()
    if args.is_delete_all:
        output = mongo.delete_all()
        print(f"mc['ebloc_broker']['cache']_is_delete={output}")
