#!/usr/bin/env python3

import os, time, math, random, sys
from random import randint
from os.path import expanduser
home = expanduser("~")

sys.path.insert(0, home + '/eBlocBroker/')
sys.path.insert(0, home + '/eBlocBroker/contractCalls')
sys.path.insert(0, home + '/eBlocBroker/test')

from submitJob   import submitJob
from blockNumber import blockNumber

def log(strIn, path, printFlag=0):
    if printFlag == 0:
        print(strIn)
    txFile = open(path + '/clientOutput.txt', 'a')
    txFile.write( strIn + "\n" )
    txFile.close()

def testFunc(path, readTest, workloadTest, testType, clusterID, cacheType):
    jobKeyNum = {} #create a dictionary called jobKeyNum
    lineNumCounter = 0
    with open(path + '/' + readTest) as test:
        for line in test:
            jobKeyNum[lineNumCounter] = line.rstrip() # Assign value to key counter.
            lineNumCounter += 1

    f            = open(path + "/" + workloadTest) # Give fixed file name
    line1        = f.readline()
    line1_in     = line1.split(" ")
    counter      = 1 #150
    printCounter = counter
    skippedLines = 0    

    while True:      
      if counter >= 0:
          if counter - skippedLines >= (len(jobKeyNum)):              
             log("Exceed hashOutput.txt's limit Total item number: " + str(len(jobKeyNum)), path)
             break
          line2          = f.readline()
          line2_splitted = line2.split(" ")
          jobKey = jobKeyNum[counter].split(" ")                            
          # Requested core shouldn't be 0.
          if int(line2_splitted[3]) > 60 and str(jobKey[1]) != '0' and (line2_splitted[0] != line2_splitted[1]) and (int(jobKey[2]) != 0):              
             if not line2:
                break  # EOF
             line2_in = line2.split(" ")
             sleepTime = str(int(line2_in[0]) -  int(line1_in[0])) # time to sleep in seconds
             
             blockNumber_ = blockNumber()
             log("\n------------------------------------------", path)
             log("Job: " + str(counter) + "| Current Time: " + time.ctime() +"| BlockNumber: " + blockNumber_, path)
             log("Nasa Submit range: " + line2_splitted[0] + " " + line2_splitted[1], path)
             log("Sleep Time to submit next job: " + sleepTime, path)
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
                
             jobKey_  = str(jobKey[0])
             coreNum = int(jobKey[2])
             
             dataTransferIn  = 10
             dataTransferOut = 10
             gasStorageHour  = 0
             # jobDescription = 'Science'

             if eudatFlag == 0:
                coreMinuteGas = int(math.ceil(float(jobKey[1]) / 60))
                log("RunTimeInMinutes: " + str(coreMinuteGas), path)
             else:
                log("RunTimeInMinutes: " + '360', path)
                coreMinuteGas   = 360 # 6 hours for nasEUDAT simulation test.
             accountID = randint(0, 9)
             log("hash: " + jobKey[0] + "| TimeToRun: " + str(coreMinuteGas) + "| Core: " + str(coreNum) + "| accountID: " + str(accountID), path)
             
             log('submitJob(' + clusterID + ', ' + jobKey_ + ', ' + str(coreNum) + ', ' + str(coreMinuteGas) + ', ' + str(dataTransferIn) + ', ' +
                 str(dataTransferOut) + ',' + str(storageID) + ', ' + jobKey_ + ', ' + str(gasStorageHour) + ', ' +
                 str(accountID) + ')', path)

             tx, computationalCost, storageCost, cacheCost, dataTransferCost, jobPriceValue = submitJob(clusterID, jobKey_, int(coreNum), coreMinuteGas,
                                                                                                        dataTransferIn, dataTransferOut, storageID,
                                                                                                        jobKey_, cacheType, gasStorageHour, accountID)
             log('computationalCost:' + computationalCost, path, 0)
             log('storageCost:'       + storageCost, path, 0)
             log('cacheCost:'         + cacheCost, path, 0)
             log('dataTransferCost:'  + dataTransferCost, path, 0)             
             log('jobPriceValue:'     + jobPriceValue, path, 1)
             log('Tx_hash:' + tx, path)

             txFile     = open(path + '/' + clusterID + '.txt', 'a')
             txFile.write(tx + " " + str(accountID) + "\n")
             txFile.close()

             sleepSeconds = int(sleepTime)
             for remaining in range(sleepSeconds, 0, -1):
                sys.stdout.write("\r")
                sys.stdout.write("{:2d} seconds remaining...".format(remaining))
                sys.stdout.flush()
                time.sleep(1)
             sys.stdout.write("\rSleeping is done!\n")
             line1    = line2
             line1_in = line2_in
             counter += 1
          else:
             skippedLines += 1
      else:
         line1   = f.readline()
         line1_in = line1.split(" ")         
    log("END", path)
    log(".", path)
    f.close()
