from pymongo import MongoClient

mc = MongoClient()
coll = mc["eBlocBroker"]["cache"]


def check_ok(result):
    if result["ok"] == 1.0:
        return True
    else:
        return False


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
    output = coll.update({"job_key": new_item["job_key"]}, new_item, True)
    return check_ok(output)


def delete_all():
    output = coll.delete_many({})
    return check_ok(output)


def delete_one(job_key):
    output = coll.delete_one({"job_key": job_key})
    return check_ok(output)


def add_item_share_id(key, shareID, share_token):
    coll = mc["eBlocBroker"]["shareID"]
    new_item = {"key": key, "shareID": shareID, "share_token": share_token}
    output = coll.update({"key": new_item["key"]}, new_item, True)
    return check_ok(output)


def find_key(coll, key):
    output = coll.find_one({"key": key})
    if bool(output):
        return True, output
    else:
        return False, None
