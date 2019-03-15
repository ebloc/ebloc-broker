#!/usr/bin/env python3

import os, time, math, random, sys
from random import randint
from os.path import expanduser
home = expanduser("~")

sys.path.insert(0, home + '/eBlocBroker/')
sys.path.insert(0, home + '/eBlocBroker/contractCalls')
sys.path.insert(0, home + '/eBlocBroker/test')

import lib
from submitJob   import submitJob
from blockNumber import blockNumber
from imports import getWeb3
web3 = getWeb3()

f = open(home + '/TESTS/accountPassword.txt', 'r') # Password read from the file.
accountPassword = f.read().replace("\n", "").replace(" ", "")
f.close()

def log(strIn, path, printFlag=0):
    if printFlag == 0:
        print(strIn)
    txFile = open(path + '/clientOutput.txt', 'a')
    txFile.write( strIn + "\n" )
    txFile.close()

def testFunc(path, readTest, workloadTest, testType, clusterID, cacheType):
    jobKeyNum = {} #create a dictionary called jobKeyNum
    counter = 0
    with open(path + '/' + readTest) as test:
        for line in test:
            eudatFlag = 0
            if (testType == 'eudat-nasa'):
                storageID = 1
                eudatFlag = 0
            elif (testType == 'eudat-nas'):
                storageID = 1
                eudatFlag = 1
            elif (testType == 'ipfs'):
                storageID = 0
            elif (testType == 'ipfsMiniLock'):
                storageID = 2
            elif (testType == 'gdrive'):
                storageID = 4

            dataTransferIn  = 10
            dataTransferOut = 10
            gasStorageHour  = 0

            jobKey = line.rstrip().split(" ")
            sleepTime = jobKey[5] # time to sleep in seconds
            blockNumber_ = blockNumber()
            if counter != 0:
                log("\n------------------------------------------", path)
            log("Job: " + str(counter + 1) + "| Current Time: " + time.ctime() +"| BlockNumber: " + blockNumber_, path)
            log("Nasa Submit range: " + jobKey[3] + " " + jobKey[4], path)
            log("Sleep Time to submit next job: " + sleepTime, path)

            jobKey_  = str(jobKey[0])
            coreNum  = int(jobKey[2])

            if eudatFlag == 0:
                coreMinuteGas = int(math.ceil(float(jobKey[1]) / 60))
                log("RunTimeInMinutes: " + str(coreMinuteGas), path)
            else:
                log("RunTimeInMinutes: " + '360', path)
                coreMinuteGas   = 360 # 6 hours for nasEUDAT simulation test.
            accountID = randint(0, 9)
            res= web3.personal.unlockAccount(web3.eth.accounts[accountID], accountPassword) # unlocks the selected account
            log("AccountID:" + str(accountID) + " (" + web3.eth.accounts[accountID] + ") is unlocked=>" + str(res), path)
            log("hash: " + jobKey[0] + "| TimeToRun: " + str(coreMinuteGas) + "| TimeToRunSeconds: " + str(math.ceil(float(jobKey[1]))) +
                "| Core: " + str(coreNum) + "| accountID: " + str(accountID), path)
            # ===========
            log('submitJob(' + clusterID + ', ' + jobKey_ + ', ' + str(coreNum) + ', ' + str(coreMinuteGas) + ', ' + str(dataTransferIn) + ', ' +
                str(dataTransferOut) + ', ' + str(storageID) + ', ' + jobKey_ + ', ' + str(gasStorageHour) + ', ' +
                str(accountID) + ')', path)

            ret = submitJob(clusterID, jobKey_, int(coreNum), coreMinuteGas, dataTransferIn, dataTransferOut, storageID,
                            jobKey_, cacheType, gasStorageHour, accountID)
            tx_hash = ret[0]
            log('Tx_hash:'           + tx_hash, path, 0)
            log('computationalCost:' + ret[1], path, 0)
            log('storageCost:'       + ret[2], path, 0)
            log('cacheCost:'         + ret[3], path, 0)
            log('dataTransferCost:'  + ret[4], path, 0)
            log('jobPriceValue:'     + ret[5], path, 1)

            txFile = open(path + '/' + clusterID + '.txt', 'a')
            txFile.write(ret[0] + " " + str(accountID) + "\n")
            txFile.close()
            sleepSeconds = int(sleepTime)

            for remaining in range(sleepSeconds, 0, -1):
                sys.stdout.write("\r")
                sys.stdout.write("{:2d} seconds remaining...".format(remaining))
                sys.stdout.flush()
                time.sleep(1)
            sys.stdout.write("\rSleeping is done!\n")
            receipt = web3.eth.getTransactionReceipt(tx_hash)
            if receipt is not None:
                res = lib.isTransactionPassed(web3, tx_hash)
                log('Tx status:' + str(res), path)
            else:
                log('Tx is not deployed yet', path)
            # ===========
            counter += 1
    log("END", path)
    log(".", path)
    f.close()
