#!/usr/bin/env python3

import sys, os, lib, logging
from imports import connect
logger = logging.Logger('catch_all')

def getJobSourceCodeHash(jobInfo, provider, jobKey, index, jobID, receivedBlockNumber, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return False, 'notconnected'
    
    try:
        event_filter = eBlocBroker.events.LogJob.createFilter(fromBlock=int(receivedBlockNumber), toBlock="latest", argument_filters={'provider': str(provider)})
        loggedJobs = event_filter.get_all_entries()
        for i in range(0, len(loggedJobs)):
            if loggedJobs[i].args['jobKey'] == jobKey and loggedJobs[i].args['index'] == int(index):
                jobInfo.update( {'sourceCodeHash' : loggedJobs[i].args['sourceCodeHash']} )
                return True, jobInfo
    except Exception as e:
        # logger.error('Failed to getJobInfo: ' + str(e))
        return False, 'Failed to getJobSourceCodeHash: ' + str(e)

def getJobInfo(provider, jobKey, index, jobID, eBlocBroker=None, w3=None, receivedBlockNumber=3082590):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return False, 'notconnected'
    
    try:
        provider = w3.toChecksumAddress(provider)

        job = eBlocBroker.functions.getJobInfo(provider, jobKey, int(index), int(jobID)).call()        
        jobPrices = eBlocBroker.functions.getProviderPricesForJob(provider, jobKey, int(index)).call()
        jobInfo = {'stateCode':           job[0],
                   'core':                job[1],
                   'startTime':           job[2],
                   'received':            job[3],
                   'executionTimeMin':    job[4],
                   'jobOwner':            job[5],
                   'dataTransferIn':      job[6],
                   'dataTransferOut':     job[7],                   
                   'priceCoreMin':        jobPrices[0],
                   'priceDataTransfer':   jobPrices[1],
                   'priceStorage':        jobPrices[2],
                   'priceCache':           jobPrices[3],
                   'resultIpfsHash':       "",
                   'endTime':              None,
                   'refundedWei':          None,
                   'receivedBlock':        None,
                   'cacheDuration':        None,
                   'sourceCodeHash':       None,
                   'dataTransferIn_used':  None,
                   'dataTransferOut_used': None
                   }

        resultIpfsHash = ""   
        event_filter = eBlocBroker.events.LogReceipt.createFilter(fromBlock=int(receivedBlockNumber), toBlock="latest", argument_filters={'provider': str(provider)})
        loggedReceipts = event_filter.get_all_entries()    
        for i in range(0, len(loggedReceipts)):
            if loggedReceipts[i].args['jobKey'] == jobKey and loggedReceipts[i].args['index'] == int(index):
                jobInfo.update( {'resultIpfsHash'       : loggedReceipts[i].args['resultIpfsHash']} )
                jobInfo.update( {'endTime'              : loggedReceipts[i].args['endTime']} )
                jobInfo.update( {'receivedWei'          : loggedReceipts[i].args['receivedWei']} )
                jobInfo.update( {'refundedWei'          : loggedReceipts[i].args['refundedWei']} )
                jobInfo.update( {'dataTransferIn_used'  : loggedReceipts[i].args['dataTransferIn']} )
                jobInfo.update( {'dataTransferOut_used' : loggedReceipts[i].args['dataTransferOut']} )
                break
            
    except Exception as e:
        # logger.error('Failed to getJobInfo: ' + str(e))
        return False, 'Failed to getJobInfo: ' + str(e)

    if str(jobInfo['core']) == '0':
        return False, 'Failed to getJobInfo: Out of index'

    return True, jobInfo

if __name__ == '__main__':
    if len(sys.argv) == 5:
        provider = str(sys.argv[1])
        jobKey   = str(sys.argv[2])
        index    = int(sys.argv[3])
        jobID    = int(sys.argv[4])        
    else:
        print('Please provide {jobKey, index, and jobID} as an argument')
        sys.exit()

    receivedBlockNumber = 3157313
    status, jobInfo = getJobInfo(provider, jobKey, index, jobID, None, None, receivedBlockNumber)

    if not status:
        print(jobInfo)
        sys.exit()

    if type(jobInfo) is dict:
        print('{0: <22}'.format('stateCode:')           + lib.inv_job_state_code[jobInfo['stateCode']] + ' (' + str(jobInfo['stateCode']) + ')'  )
        print('{0: <22}'.format('core')                 + str(jobInfo['core']))
        print('{0: <22}'.format('startTime')            + str(jobInfo['startTime']))
        print('{0: <22}'.format('endTime:')             + str(jobInfo['endTime']))
        print('{0: <22}'.format('receivedWei:')         + str(jobInfo['receivedWei']))
        print('{0: <22}'.format('refundedWei:')         + str(jobInfo['refundedWei']))
        print('{0: <22}'.format('executionTimeMin:')    + str(jobInfo['executionTimeMin']))
        print('{0: <22}'.format('jobInfoOwner:')        + str(jobInfo['jobOwner']))
        print('{0: <22}'.format('priceCoreMin:')        + str(jobInfo['priceCoreMin']))
        print('{0: <22}'.format('priceDataTransfer:')   + str(jobInfo['priceDataTransfer']))
        print('{0: <22}'.format('priceStorage:')        + str(jobInfo['priceStorage']))
        print('{0: <22}'.format('priceCache:')          + str(jobInfo['priceCache']))
        print('{0: <22}'.format('resultIpfsHash:')      + lib.convertBytes32ToIpfs(jobInfo['resultIpfsHash']))       
        print('{0: <22}'.format('dataTransferIn:')      + str(jobInfo['dataTransferIn']))
        print('{0: <22}'.format('dataTransferOut:')     + str(jobInfo['dataTransferOut']))
        print('{0: <22}'.format('dataTransferIn_used:')      + str(jobInfo['dataTransferIn_used']))
        print('{0: <22}'.format('dataTransferOut_used:')      + str(jobInfo['dataTransferOut_used']))                
        print('{0: <22}'.format('sourceCodeHashArray:') + str(jobInfo['dataTransferOut']))
        
        status, jobInfo = getJobSourceCodeHash(jobInfo, provider, jobKey, index, jobID, receivedBlockNumber)
        print('{0: <22}'.format('sourceCodeHash:')      + str(jobInfo['sourceCodeHash']))        
    else:
        print(jobInfo)
