from pymongo import MongoClient
cl = MongoClient()
coll = cl['eBlocBroker']['cache']

def addItem(jobKey, sourceCodeHash, userID, timestamp, storageTime, storageID):
    newItem = {'jobKey'        : jobKey,
               'sourceCodeHash': sourceCodeHash,
               'userID'        : userID,
               'timestamp'     : timestamp,
               'storageTime'   : storageTime,
               'storageID'     : storageID
    }
    x = coll.update({'jobKey':newItem['jobKey']}, newItem, True)

def deleteAll():
    coll.delete_many({})

def deleteOne(jobKey):
    result = coll.delete_one({'jobKey':jobKey})
