from pymongo import MongoClient
cl = MongoClient()
coll = cl['eBlocBroker']['cache']

def addItem(jobKey, sourceCodeHash_list, requesterID, timestamp, storageID, jobInfo):       
    newItem = {'jobKey'        : jobKey,
               'sourceCodeHash': sourceCodeHash_list,
               'requesterID'   : requesterID,
               'timestamp'     : timestamp,               
               'storageID'     : storageID,
               'receivedBlock' : jobInfo[0]['receivedBlock'],
               'cacheDuration' : jobInfo[0]['cacheDuration']
    }
    x = coll.update({'jobKey':newItem['jobKey']}, newItem, True)

def deleteAll():
    coll.delete_many({})

def deleteOne(jobKey):
    result = coll.delete_one({'jobKey':jobKey})
