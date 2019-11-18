#!/usr/bin/env python3

import sys, os, lib, _thread, time, hashlib, subprocess, lib_mongodb, lib

from lib import silentremove
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
    receivedBlockNum, storageTime = getJobStorageTime(lib.PROVIDER_ID, document['sourceCodeHash'])
    endBlockTime = receivedBlockNum + storageTime * 240
    storageID = document['storageID']
    if endBlockTime < blockNum and receivedBlockNum != 0:        
        if storageID == lib.storageID.ipfs or storageID == lib.storageID.ipfs_miniLock:
            ipfsHash = document['jobKey']
            command = ['ipfs', 'pin', 'rm', ipfsHash]
            status, res = lib.executeShellCommand(command)     
            print(res)
            status, res = lib.executeShellCommand(['ipfs', 'repo', 'gc'])
            print(res)
        else:
            cachedFileName = lib.PROGRAM_PATH + '/' + document['requesterID'] + '/cache/' + document['sourceCodeHash'] + 'tar.gz'            
            print(cachedFileName)
            silentremove(cachedFileName)
            cachedFileName = lib.PROGRAM_PATH + '/cache/' + document['sourceCodeHash'] + 'tar.gz'
            print(cachedFileName)
            silentremove(cachedFileName)
                       
        print(receivedBlockNum)
        result = coll.delete_one({'jobKey':ipfsHash})
        

        
        


