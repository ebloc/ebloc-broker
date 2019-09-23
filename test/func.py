#!/usr/bin/env python3

import os, time, math, random, sys
from random import randint
from os.path import expanduser
home = expanduser("~")

import lib
from imports import getWeb3
from contractCalls.submitJob   import submitJob
from contractCalls.blockNumber import blockNumber

w3 = getWeb3()

f = open(home + '/TESTS/accountPassword.txt', 'r') # Password read from the file.
accountPassword = f.read().replace("\n", "").replace(" ", "")
f.close()

def log(my_string, path, printFlag=0):
    if printFlag == 0:
        print(my_string)
        
    f = open(path + '/clientOutput.txt', 'a')
    f.write( my_string + "\n" )
    f.close()

def testFunc(path, readTest, testType, providerID, cacheType):
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
            sourceCodeHash = jobKey[5] # time to sleep in seconds
            sleepTime = jobKey[6] # time to sleep in seconds
            blockNumber_ = blockNumber()
            if counter != 0:
                log("\n------------------------------------------", path)
                
            log("Job: " + str(counter + 1) + "| Current Time: " + time.ctime() +"| BlockNumber: " + blockNumber_, path)
            log("Nasa Submit range: " + jobKey[3] + " " + jobKey[4], path)
            log("Sleep Time to submit next job: " + sleepTime, path)
            log("Sourcecode Hash=" + sourceCodeHash, path)
            jobKey_  = str(jobKey[0])
            coreNum  = int(jobKey[2])
            if eudatFlag == 0:
                coreMinuteGas = int(math.ceil(float(jobKey[1]) / 60))
                log("RunTimeInMinutes: " + str(coreMinuteGas), path)
            else:
                log("RunTimeInMinutes: " + '360', path)
                coreMinuteGas   = 360 # 6 hours for nasEUDAT simulation test.
                
            accountID = randint(0, 9)
            res= w3.personal.unlockAccount(w3.eth.accounts[accountID], accountPassword) # unlocks the selected account in case if unlocks over time
            log("AccountID:" + str(accountID) + " (" + w3.eth.accounts[accountID] + ") is unlocked=>" + str(res), path)
            log("hash=" + jobKey[0] + "| TimeToRun=" + str(coreMinuteGas) + "| TimeToRunSeconds=" + str(math.ceil(float(jobKey[1]))) + "| Core=" + str(coreNum) + "| accountID=" + str(accountID), path)
            # ===========
            log('submitJob(' + providerID + ', ' + jobKey_ + ', ' + str(coreNum) + ', ' + str(coreMinuteGas) + ', ' + str(dataTransferIn) + ', ' +
                str(dataTransferOut) + ', ' + str(storageID) + ', ' + jobKey_ + ', ' + str(gasStorageHour) + ', ' +
                str(accountID) + ')', path)

            status, ret = submitJob(provider, jobKey, core_list, coreMin_list, dataTransferIn, dataTransferOut, storageID, sourceCodeHash_list,
cacheType, cacheHour_list, accountID, jobPriceValue, eBlocBroker, w3)
                
            # ret = submitJob(providerID, jobKey_, int(coreNum), coreMinuteGas, dataTransferIn, dataTransferOut, storageID, sourceCodeHash, cacheType, gasStorageHour, accountID) # delete

            if not status:
                log(ret, path, 0)
            else:
                tx_hash = ret[0]
                log('Tx_hash:'           + tx_hash, path, 0)
                log('computationalCost:' + ret[1], path, 0)
                log('storageCost:'       + ret[2], path, 0)
                log('cacheCost:'         + ret[3], path, 0)
                log('dataTransferCost:'  + ret[4], path, 0)
                log('jobPriceValue:'     + ret[5], path, 1)

            txFile = open(path + '/' + providerID + '.txt', 'a')
            txFile.write(ret[0] + " " + str(accountID) + "\n")
            txFile.close()
            sleepSeconds = int(sleepTime)

            for remaining in range(sleepSeconds, 0, -1):
                sys.stdout.write("\r")
                sys.stdout.write("{:2d} seconds remaining...".format(remaining))
                sys.stdout.flush()
                time.sleep(1)
            sys.stdout.write("\rSleeping is done!\n")
            receipt = w3.eth.getTransactionReceipt(tx_hash)
            if receipt is not None:
                res = lib.isTransactionPassed(w3, tx_hash)
                log('Tx status:' + str(res), path)
            else:
                log('Tx is not deployed yet', path)
            # ===========
            counter += 1
    log("END", path)
    log(".", path)
    f.close()
