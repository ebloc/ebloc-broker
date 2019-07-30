#!/usr/bin/env python3

import sys, os, lib, _thread, time, hashlib, subprocess
import lib_mongodb, lib

from pymongo import MongoClient
cl = MongoClient()
coll = cl['eBlocBroker']['cache']

from imports import connectEblocBroker, getWeb3
from contractCalls.blockNumber       import blockNumber
from contractCalls.getJobStorageTime import getJobStorageTime

web3        = getWeb3() 
eBlocBroker = connectEblocBroker() 

'''find_all'''
blockNum = int(blockNumber())
print(str(blockNum))

cursor = coll.find({})
for document in cursor:
    # print(document)
    receivedBlockNum, storageTime = getJobStorageTime(lib.CLUSTER_ID, document['sourceCodeHash'])
    endBlockTime = receivedBlockNum + storageTime *240
    storageID = document['storageID']
    if endBlockTime < blockNum and receivedBlockNum != 0:        
        if storageID == lib.storageID.ipfs or storageID == lib.storageID.ipfs_miniLock:
            ipfsHash = document['jobKey']
            command = ['ipfs', 'pin', 'rm', ipfsHash]
            res = lib.runCommand(command)     
            print(res)
            res = lib.runCommand(['ipfs', 'repo', 'gc'])
            print(res)
        else:
            cachedFileName = lib.PROGRAM_PATH + '/' + document['userID'] + '/cache/' + document['sourceCodeHash'] + 'tar.gz'            
            print(cachedFileName)
            lib.silentremove(cachedFileName)
            cachedFileName = lib.PROGRAM_PATH + '/cache/' + document['sourceCodeHash'] + 'tar.gz'
            print(cachedFileName)
            lib.silentremove(cachedFileName)
                       
        print(receivedBlockNum)        
        result = coll.delete_one({'jobKey':ipfsHash})       
