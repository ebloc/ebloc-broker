from pprint import pprint

from pymongo import MongoClient

mc = MongoClient()
collection = mc["eBlocBroker"]["cache"]


def check_ok(result):
    return bool(result["ok"])


def add_item(job_key, index, source_code_hash_list, requester_id, timestamp, cloudStorageID, job_info):
    new_item = {
        "requester_address": job_info["jobOwner"],
        "requester_id": requester_id,
        "job_key": job_key,
        "index": index,
        "source_code_hash": source_code_hash_list,
        "received_block_number": job_info["received_block_number"],
        "timestamp": timestamp,
        "cloudStorageID": cloudStorageID,
        "cacheDuration": job_info["cacheDuration"],
        "receieved": False
    }
    output = collection.update({"job_key": new_item["job_key"]}, new_item, True)
    return check_ok(output)


def delete_all():
    return collection.delete_many({}).acknowledged


def delete_one(job_key):
    output = collection.delete_one({"job_key": job_key})
    return check_ok(output)


def add_item_share_id(key, shareID, share_token):
    coll = mc["eBlocBroker"]["shareID"]
    new_item = {"job_key": key, "shareID": shareID, "share_token": share_token}
    output = coll.update({"job_key": new_item["job_key"]}, new_item, True)
    return check_ok(output)


def find_key(_coll, key):
    output = _coll.find_one({"job_key": key})
    if bool(output):
        return output
    else:
        raise


def get_job_block_number(requester_address, key, index) -> int:
    cursor = collection.find({"requester_address":requester_address.lower(), "job_key":key, "index":index})
    for document in cursor:
        return document["received_block_number"]
    else:
        return 0


def is_received(requester_address, key, index, is_print=False) -> bool:
    cursor = collection.find({"requester_address":requester_address.lower(), "job_key":key, "index":index})
    if is_print:
        for document in cursor:
            pprint(document)

    if cursor.count() == 0:
        return False
    return True


def find_all():
    """find_all"""
    # coll = mc["eBlocBroker"]["shareID"]
    print("printing all")
    cursor = collection.find({})

    for document in cursor:
        pprint(document)
    # print(document['_id'])
    # print(document['timestamp'])
