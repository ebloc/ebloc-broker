#!/usr/bin/env python3

import sys, os
from pymongo import MongoClient
import lib_mongodb

cl = MongoClient()
coll = cl['eBlocBroker']['cache']
  
'''find_all'''
print('printing all')
cursor = coll.find({})
for document in cursor:
    print(document)
    # print(document['_id'])
    # print(document['timestamp'])  
