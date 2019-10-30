#!/usr/bin/env python3

import sys, os, lib, logging, traceback
from imports import connect
logger = logging.Logger('catch_all')

def getJobSourceCodeHash(jobInfo, provider, jobKey, index, jobID, receivedBlockNumber=None, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return False, 'notconnected'

    if receivedBlockNumber is None:
        receivedBlockNumber = 3082590 # Point where the eBlocBroker contract deployed
        _toBlock = "latest"
    else:
        _toBlock = int(receivedBlockNumber)

    try:
        event_filter = eBlocBroker.events.LogJob.createFilter(fromBlock=int(receivedBlockNumber), toBlock=_toBlock, argument_filters={'provider': str(provider)})
        loggedJobs = event_filter.get_all_entries()
        for i in range(0, len(loggedJobs)):
            if loggedJobs[i].args['jobKey'] == jobKey and loggedJobs[i].args['index'] == int(index):
                jobInfo.update( {'sourceCodeHash' : loggedJobs[i].args['sourceCodeHash']} )
                return True, jobInfo
    except Exception as e:
        # logger.error('Failed to getJobInfo: ' + str(e))
        return False, 'Failed to getJobSourceCodeHash: ' + str(e)

def getJobInfo(provider, jobKey, index, jobID, receivedBlockNumber=None, eBlocBroker=None, w3=None):
    if receivedBlockNumber is None:
        receivedBlockNumber = 3082590 # Point where the eBlocBroker contract deployed
        _toBlock = "latest"
    else:
        _toBlock = int(receivedBlockNumber)
    
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return False, 'notconnected'
    try:
        provider = w3.toChecksumAddress(provider)

        job = eBlocBroker.functions.getJobInfo(provider, jobKey, int(index), int(jobID)).call()
        jobPrices = eBlocBroker.functions.getProviderPricesForJob(provider, jobKey, int(index)).call()
        print(job)
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
                   'priceCache':          jobPrices[3],
                   'resultIpfsHash':       "",
                   'endTime':              None,
                   'refundedWei':          None,
                   'receivedBlock':        None,
                   'receivedWei':          None,
                   'cacheDuration':        None,
                   'sourceCodeHash':       None,
                   'dataTransferIn_used':  None,
                   'dataTransferOut_used': None
                   }

        resultIpfsHash = ""
        event_filter = eBlocBroker.events.LogReceipt.createFilter(fromBlock=int(receivedBlockNumber), toBlock='latest', argument_filters={'provider': str(provider)})
    
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

    except Exception:
        # logger.error('Failed to getJobInfo: ' + str(e))
        return False, 'E: Failed to getJobInfo: ' + traceback.format_exc()

    if str(jobInfo['core']) == '0':
        return False, 'E: Failed to getJobInfo: Out of index'

    return True, jobInfo

if __name__ == '__main__':
    if len(sys.argv) == 5 or len(sys.argv) == 6:
        provider = str(sys.argv[1])
        jobKey   = str(sys.argv[2])
        index    = int(sys.argv[3])
        jobID    = int(sys.argv[4])
        if len(sys.argv) == 6:
            receivedBlockNumber = int(sys.argv[5])
        else:
            receivedBlockNumber = None
    else:
        print('Please provide {provider, jobKey, index, and jobID} as arguments')
        sys.exit()

    # receivedBlockNumber = 3157313
    status, jobInfo = getJobInfo(provider, jobKey, index, jobID, receivedBlockNumber)

    if not status:
        print(jobInfo)
        sys.exit()

    if jobInfo['resultIpfsHash'] != "":
        _resultIpfsHash = lib.convertBytes32ToIpfs(jobInfo['resultIpfsHash'])
    else:
        _resultIpfsHash = ""                                                      
    
    if type(jobInfo) is dict:
        print('{0: <22}'.format('stateCode:')           + lib.inv_job_state_code[jobInfo['stateCode']] + ' (' + str(jobInfo['stateCode']) + ')'  )
        print('{0: <22}'.format('core')                  + str(jobInfo['core']))
        print('{0: <22}'.format('startTime')             + str(jobInfo['startTime']))
        print('{0: <22}'.format('endTime:')              + str(jobInfo['endTime']))
        print('{0: <22}'.format('receivedWei:')          + str(jobInfo['receivedWei']))
        print('{0: <22}'.format('refundedWei:')          + str(jobInfo['refundedWei']))
        print('{0: <22}'.format('executionTimeMin:')     + str(jobInfo['executionTimeMin']))
        print('{0: <22}'.format('jobInfoOwner:')         + str(jobInfo['jobOwner']))
        print('{0: <22}'.format('priceCoreMin:')         + str(jobInfo['priceCoreMin']))
        print('{0: <22}'.format('priceDataTransfer:')    + str(jobInfo['priceDataTransfer']))
        print('{0: <22}'.format('priceStorage:')         + str(jobInfo['priceStorage']))
        print('{0: <22}'.format('priceCache:')           + str(jobInfo['priceCache']))
        print('{0: <22}'.format('resultIpfsHash:')       + _resultIpfsHash)       
        print('{0: <22}'.format('dataTransferIn:')       + str(jobInfo['dataTransferIn']))
        print('{0: <22}'.format('dataTransferOut:')      + str(jobInfo['dataTransferOut']))
        print('{0: <22}'.format('dataTransferIn_used:')  + str(jobInfo['dataTransferIn_used']))
        print('{0: <22}'.format('dataTransferOut_used:') + str(jobInfo['dataTransferOut_used']))                
        print('{0: <22}'.format('sourceCodeHashArray:')  + str(jobInfo['dataTransferOut']))
        
        status, jobInfo = getJobSourceCodeHash(jobInfo, provider, jobKey, index, jobID, receivedBlockNumber)
        print('{0: <22}'.format('sourceCodeHash:')      + str(jobInfo['sourceCodeHash']))        
    else:
        print(jobInfo)
