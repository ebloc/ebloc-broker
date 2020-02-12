from pymongo import MongoClient

mc = MongoClient()
coll = mc["eBlocBroker"]["cache"]


def add_item(job_key, source_code_hash_list, requesterID, timestamp, cloudStorageID, job_info):
    new_item = {
        "job_key": job_key,
        "source_code_hash": source_code_hash_list,
        "requesterID": requesterID,
        "timestamp": timestamp,
        "cloudStorageID": cloudStorageID,
        "receivedBlock": job_info["receivedBlock"],
        "cacheDuration": job_info["cacheDuration"],
    }
    result = coll.update({"job_key": new_item["job_key"]}, new_item, True)


def delete_all():
    coll.delete_many({})


def delete_one(job_key):
    result = coll.delete_one({"job_key": job_key})
