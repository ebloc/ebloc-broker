#!/usr/bin/env python3

import math
import time
from os.path import expanduser
from random import randint

import eblocbroker.Contract as Contract
from imports import connect_to_web3
from utils import is_transaction_passed, sleep_timer

home = expanduser("~")
w3 = connect_to_web3()
Ebb = Contract.eblocbroker


f = open(f"{home}/TESTS/accountPassword.txt", "r")  # password read from the file
accountPassword = f.read().strip()
f.close()


def log(my_string, path, print_flag=0):
    if print_flag == 0:
        print(my_string)

    f = open(f"{path}/clientOutput.txt", "a")
    f.write(my_string + "\n")
    f.close()


def testFunc(path, readTest, testType, providerID, cacheType):
    with open(path + "/" + readTest) as test:
        for idx, line in enumerate(test):
            if idx != 0:
                log("\n------------------------------------------", path)

            eudatFlag = 0
            if testType == "eudat-nasa":
                cloudStorageID = 1
                eudatFlag = 0
            elif testType == "eudat-nas":
                cloudStorageID = 1
                eudatFlag = 1
            elif testType == "ipfs":
                cloudStorageID = 0
            elif testType == "gdrive":
                cloudStorageID = 4

            dataTransferIn = 10
            dataTransferOut = 10
            gasStorageHour = 0

            jobKey = line.rstrip().split(" ")
            sourceCodeHash = jobKey[5]  # time to sleep in seconds
            sleepTime = jobKey[6]  # time to sleep in seconds
            block_number = Ebb.get_block_number()

            log(
                "Job: " + str(idx + 1) + "| Current Time: " + time.ctime() + "| BlockNumber: " + str(block_number),
                path,
            )
            log("Nasa Submit range: " + jobKey[3] + " " + jobKey[4], path)
            log("Sleep Time to submit next job: " + sleepTime, path)
            log("Sourcecode Hash=" + sourceCodeHash, path)
            jobKey_ = str(jobKey[0])
            coreNum = int(jobKey[2])
            if eudatFlag == 0:
                coreMinuteGas = int(math.ceil(float(jobKey[1]) / 60))
                log("RunTimeInMinutes: " + str(coreMinuteGas), path)
            else:
                log("RunTimeInMinutes: " + "360", path)
                coreMinuteGas = 360  # 6 hours for nasEUDAT simulation test.

            account_id = randint(0, 9)
            output = w3.personal.unlockAccount(
                w3.eth.accounts[account_id], accountPassword
            )  # unlocks the selected account in case if unlocks over time
            log(
                "AccountID:" + str(account_id) + " (" + w3.eth.accounts[account_id] + ") is unlocked=>" + str(output),
                path,
            )
            log(
                "hash="
                + jobKey[0]
                + "| TimeToRun="
                + str(coreMinuteGas)
                + "| TimeToRunSeconds="
                + str(math.ceil(float(jobKey[1])))
                + "| Core="
                + str(coreNum)
                + "| account_id="
                + str(account_id),
                path,
            )

            log(
                "submit_job("
                + providerID
                + ", "
                + jobKey_
                + ", "
                + str(coreNum)
                + ", "
                + str(coreMinuteGas)
                + ", "
                + str(dataTransferIn)
                + ", "
                + str(dataTransferOut)
                + ", "
                + str(cloudStorageID)
                + ", "
                + jobKey_
                + ", "
                + str(gasStorageHour)
                + ", "
                + str(account_id)
                + ")",
                path,
            )

            output = Ebb.submit_job(
                provider,
                jobKey,
                core_list,
                run_time,
                dataTransferIn,
                dataTransferOut,
                cloudStorageID,
                sourceCodeHash_list,
                cacheType,
                cacheHour_list,
                account_id,
                job_price,
            )

            # ret = submit_job(providerID, jobKey_, int(coreNum), coreMinuteGas, dataTransferIn, dataTransferOut, cloudStorageID, sourceCodeHash, cacheType, gasStorageHour, account_id)  # delete

            if not success:
                log(output, path, 0)
            else:
                tx_hash = output[0]
                log("tx_hash:" + tx_hash, path, 0)
                log("computationalCost:" + output[1], path, 0)
                log("storageCost:" + output[2], path, 0)
                log("cacheCost:" + output[3], path, 0)
                log("dataTransferCost:" + output[4], path, 0)
                log("job_price:" + output[5], path, 1)

            txFile = open(path + "/" + providerID + ".txt", "a")
            txFile.write(output[0] + " " + str(account_id) + "\n")
            txFile.close()
            sleep_timer(int(sleepTime))
            receipt = w3.eth.getTransactionReceipt(tx_hash)
            if receipt:
                output = is_transaction_passed(w3, tx_hash)
                log(f"tx status:{output}", path)
            else:
                log("tx is not deployed yet", path)

    log("END", path)
    log(".", path)
    f.close()
