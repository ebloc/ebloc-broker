#!/usr/bin/env python3

from pymongo import MongoClient

cl = MongoClient()
coll = cl["eBlocBroker"]["cache"]

"""find_all"""
print("printing all")
cursor = coll.find({})
for document in cursor:
    print(document)
    # print(document['_id'])
    # print(document['timestamp'])
