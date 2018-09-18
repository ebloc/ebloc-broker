#!/usr/bin/env python

import sys 

def getJobInfo(clusterAddress, jobKey, index, eBlocBroker=None, web3=None): #{
    if eBlocBroker == None and web3 == None: #{
        import os 
        sys.path.insert(1, os.path.join(sys.path[0], '..')) 
        from imports import connectEblocBroker
        from imports import getWeb3
        
        web3        = getWeb3()
        if web3 == 'notconnected':
            return 'notconnected'
        eBlocBroker = connectEblocBroker(web3)
    #}
      
    clusterAddress = web3.toChecksumAddress(clusterAddress)
    job = None
    try:
        job = eBlocBroker.functions.getJobInfo(clusterAddress, jobKey, int(index)).call()
        jobDict = {'status': job[0], 'core': job[1], 'startTime': job[2], 'received': job[3], 'coreMinutePrice': job[4], 'coreMinuteGas': job[5], 'jobOwner': job[6]}
    except Exception as e:
        # print(e)
        return e.__class__.__name__
        # return 'Exception: web3.exceptions.BadFunctionCallOutput'
    return jobDict
#}

if __name__ == '__main__': #{
    if len(sys.argv) == 3:
        clusterAddress = str(sys.argv[1]) 
        jobKey         = str(sys.argv[2]) 
        index          = int(sys.argv[3]) 
    else:
        clusterAddress = "0x4e4a0750350796164d8defc442a712b7557bf282" 
        # jobKey         = "153802737479941507912962421857730686964" 
        index          = 0
        jobKey         = 'QmRsaBEGcqxQcJbBxCi1LN9iz5bDAGDWR6Hx7ZvWqgqmdR'  # Long Sleep Job
        index          = 0
        
    jobInfo = getJobInfo(clusterAddress, jobKey, index)
        
    if type(jobInfo) is dict:   
        print('{0: <16}'.format('status:') + str(jobInfo['status']))
        print('{0: <16}'.format('core') + str(jobInfo['core']))
        print('{0: <16}'.format('startTime') + str(jobInfo['startTime']))
        print('{0: <16}'.format('received:') + str(jobInfo['received']))
        print('{0: <16}'.format('coreMinutePrice:') + str(jobInfo['coreMinutePrice']))
        print('{0: <16}'.format('coreMinuteGas:') + str(jobInfo['coreMinuteGas']))
        print('{0: <16}'.format('jobInfoOwner:') + jobInfo['jobOwner'])        
    else:
        print(jobInfo)
#}
