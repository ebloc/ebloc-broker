#!/usr/bin/env python3

import argparse

from pymongo import MongoClient
from rich.pretty import pprint
from broker._utils import _log
from broker._utils._log import log

_log.IS_WRITE = False


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
            self.find_all()
            raise Exception(f"could not find key={_key}")

    def add_item(self, key, item):
        res = self.collection.replace_one({"key": key}, item, True)
        return res.acknowledged

    def find_all(self, sort_str="", is_print=False, is_compact=False):
        """Find all the records."""
        if sort_str:
            cursor = self.collection.find({}, {"_id": False}).sort(sort_str)
        else:
            cursor = self.collection.find({}, {"_id": False})

        if is_print:
            for document in cursor:
                if is_compact:
                    log(f"{document['key']} [m]=>[/m] {document['value']}")
                else:
                    log(document)

        return cursor


class MongoBroker(BaseMongoClass):
    """Create MongoBroker class."""

    def __init__(self, mc, collection) -> None:
        super().__init__(mc, collection)
        self.share_id_coll = self.mc["ebloc_broker"]["share_id"]

    def add_item(self, job_key, index, source_code_hash_list, requester_id, timestamp, cloud_storage_id, job_info):
        """Adding job info along with its cache_duration into mongoDB."""
        item = {
            "job_key": job_key,
            "index": index,
            "requester_addr": job_info["job_owner"],
            "requester_id": requester_id,
            "source_code_hash": source_code_hash_list,
            "received_bn": job_info["received_bn"],
            "timestamp": timestamp,
            "cloudStorageID": cloud_storage_id,
            "storage_duration": job_info["storage_duration"],
            "receieved": False,
            "set_job_state_running_tx": "",
        }
        res = self.collection.replace_one({"job_key": job_key, "index": index}, item, True)
        return res.acknowledged

    def find_all_share_id(self):
        cursor = self.share_id_coll.find({})
        for document in cursor:
            log(document)

    def find_shareid_item(self, key):
        output = self.share_id_coll.find_one({"job_key": key})
        if bool(output):
            return output
        else:
            raise Exception(f"warning: could not find id in MongoBroker, key={key}")

    def find_id(self, key: str, index: int):
        output = self.collection.find_one({"job_key": key, "index": index})
        if bool(output):
            return output
        else:
            # self.find_all()
            raise Exception(f"Coudn't find id. key={key} index={index}")

    def delete_one(self, job_key, index: int):
        output = self.collection.delete_one({"job_key": job_key, "index": index})
        return output.acknowledged

    def get_job_state_running_tx(self, key: str, index: int):
        """Get tx hash of the job.status as running."""
        output = self.find_id(key, index)
        return output["set_job_state_running_tx"]

    def get_job_state_running_pid(self, key: str, index: int):
        """Get tx hash of the job.status as running."""
        output = self.find_id(key, index)
        return output["pid"]

    def set_job_state_pid(self, key: str, index: int, pid: int):
        """Set tx hash of the job.status as running."""
        output = self.find_id(key, index)
        res = self.collection.update_one({"_id": output["_id"]}, {"$set": {"pid": pid}}, upsert=False)
        return res.acknowledged

    def set_job_state_running_tx(self, key: str, index: int, value: str):
        """Set tx hash of the job.status as running."""
        output = self.find_id(key, index)
        res = self.collection.update_one(
            {"_id": output["_id"]}, {"$set": {"set_job_state_running_tx": value}}, upsert=False
        )
        return res.acknowledged

    def add_item_share_id(self, key, share_id, share_token):
        # TODO: check
        item = {"job_key": key, "share_id": share_id, "share_token": share_token}
        res = self.share_id_coll.replace_one({"job_key": key}, item, True)  # , "index": 0
        return res.acknowledged

    def get_job_bn(self, requester_addr, key, index) -> int:
        cursor = self.collection.find({"requester_addr": requester_addr.lower(), "job_key": key, "index": index})
        for document in cursor:
            return document["received_bn"]

        return 0

    def delete_shared_ids(self):
        return self.share_id_coll.delete_many({}).acknowledged

    def delete_all(self):
        return self.collection.delete_many({}).acknowledged

    def is_received(self, requester_addr, key, index, is_print=False) -> bool:
        cursor = self.collection.find({"requester_addr": requester_addr.lower(), "job_key": key, "index": index})
        if is_print:
            for document in cursor:
                pprint(document)

        if cursor.count() == 0:
            return False

        return True


def main():
    mc = MongoClient()
    ebb_mongo = MongoBroker(mc, mc["ebloc_broker"]["cache"])
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
        ebb_mongo.delete_shared_ids()
        output = ebb_mongo.delete_all()
        log(f"mc['ebloc_broker']['cache'] is_deleted={output}")
    else:
        ebb_mongo.find_all_share_id()
        # output = ebb_mongo.get_job_state_running_tx("QmRD841sowPfgz8u2bMBGA5bYAAMPXxUb4J95H7YjngU4K", 37)
        # log(output)
        # ebb_mongo.find_all()
        # Ebb = cfg.Ebb
        # output = ebb_mongo.find_id("QmRD841sowPfgz8u2bMBGA5bYAAMPXxUb4J95H7YjngU4K", 32)
        # output = ebb_mongo.set_job_state_running_tx("QmRD841sowPfgz8u2bMBGA5bYAAMPXxUb4J95H7YjngU4K", 33, "0xuser33")
        # ebb_mongo.find_all()


if __name__ == "__main__":
    main()
