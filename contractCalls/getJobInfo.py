#!/usr/bin/env python3

import sys, os
import lib

def getJobInfo(providerAddress, jobKey, index, eBlocBroker=None, web3=None):
    if eBlocBroker is None and web3 is None:
        import os
        from imports import connectEblocBroker, getWeb3
        web3        = getWeb3()
        if web3 == 'notconnected':
            return 'notconnected'
        eBlocBroker = connectEblocBroker(web3)

    providerAddress = web3.toChecksumAddress(providerAddress)
    job = None
    try:
        job = eBlocBroker.functions.getJobInfo(providerAddress, jobKey, int(index)).call()
        jobPrices = eBlocBroker.functions.getProviderPricesForJob(providerAddress, jobKey, int(index)).call()
        jobDict = {'status':            job[0],
                   'core':              job[1],
                   'startTime':         job[2],
                   'received':          job[3],
                   'coreMinuteGas':     job[4],
                   'jobOwner':          job[5],
                   'priceCoreMin':      jobPrices[0],
                   'priceDataTransfer': jobPrices[1],
                   'priceStorage':      jobPrices[2],
                   'priceCache':        jobPrices[3],
                   'resultIpfsHash':    "",
                   'endTime':           "",
                   'returned':          "",
                   'dataTransferIn':    "",
                   'dataTransferOut':   "",
                   'dataTransferSum':   ""
                   }
    except Exception as e:
        return e.__class__.__name__
        # return 'Exception: web3.exceptions.BadFunctionCallOutput'

    resultIpfsHash = ""
    myFilter = eBlocBroker.events.LogReceipt.createFilter(
        fromBlock=int(2587300),
        argument_filters={'providerAddress': str(providerAddress)})
    loggedJobs = myFilter.get_all_entries()
    for i in range(0, len(loggedJobs)):
        if loggedJobs[i].args['jobKey'] == jobKey and loggedJobs[i].args['index'] == index:
            jobDict.update( {'resultIpfsHash' : loggedJobs[i].args['resultIpfsHash']} )
            jobDict.update( {'endTime' : loggedJobs[i].args['endTime']} )
            jobDict.update( {'returned' : loggedJobs[i].args['returned']} )
            jobDict.update( {'dataTransferIn' : loggedJobs[i].args['dataTransferIn']} )
            jobDict.update( {'dataTransferOut' : loggedJobs[i].args['dataTransferOut']} )
            jobDict.update( {'dataTransferSum' : loggedJobs[i].args['dataTransferSum']} )            
            return jobDict

    return jobDict
if __name__ == '__main__':
    if len(sys.argv) == 4:
        providerAddress = str(sys.argv[1])
        jobKey         = str(sys.argv[2])
        index          = int(sys.argv[3])
    else:
        print('Please probide jobKey and index as an argument')
        sys.exit()

    jobInfo  = getJobInfo(providerAddress, jobKey, index)

    if jobInfo == "BadFunctionCallOutput":
        print("Error: " + jobInfo)
        sys.exit()

    if str(jobInfo['core']) == '0':
        print('Out of index.')
        sys.exit()

    if type(jobInfo) is dict:
        print('{0: <19}'.format('status:')            + lib.inv_job_state_code[jobInfo['status']])
        print('{0: <19}'.format('status:')            + str(jobInfo['status']))
        print('{0: <19}'.format('core')               + str(jobInfo['core']))
        print('{0: <19}'.format('startTime')          + str(jobInfo['startTime']))
        print('{0: <19}'.format('endTime:')           + str(jobInfo['endTime']))
        print('{0: <19}'.format('received:')          + str(jobInfo['received']))
        print('{0: <19}'.format('returned:')          + str(jobInfo['returned']))
        print('{0: <19}'.format('coreMinuteGas:')     + str(jobInfo['coreMinuteGas']))
        print('{0: <19}'.format('jobInfoOwner:')      + str(jobInfo['jobOwner']))
        print('{0: <19}'.format('priceCoreMin:')      + str(jobInfo['priceCoreMin']))
        print('{0: <19}'.format('priceDataTransfer:') + str(jobInfo['priceDataTransfer']))
        print('{0: <19}'.format('priceStorage:')      + str(jobInfo['priceStorage']))
        print('{0: <19}'.format('priceCache:')        + str(jobInfo['priceCache']))
        print('{0: <19}'.format('resultIpfsHash:')    + jobInfo['resultIpfsHash'])
        print('{0: <19}'.format('dataTransferIn:')    + str(jobInfo['dataTransferIn']))
        dataTransferSum = jobInfo['dataTransferSum']
        if dataTransferSum == "":
            print('{0: <19}'.format('dataTransferOut:')   + "")
        else:
            print('{0: <19}'.format('dataTransferOut:')   + str(dataTransferSum - dataTransferIn))
    else:
        print(jobInfo)
