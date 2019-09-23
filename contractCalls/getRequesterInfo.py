#!/usr/bin/env python3

import sys, os, traceback
from imports import connect, getWeb3

def getRequesterInfo(_requester, eBlocBroker=None, w3=None):
    eBlocBroker, w3 = connect(eBlocBroker, w3)
    if eBlocBroker is None or w3 is None:
        return

    _requester = w3.toChecksumAddress(_requester)
    
    if eBlocBroker.functions.isRequesterExists(_requester).call() == False:
        return False, "Requester is not registered. Please try again with registered Ethereum Address as requester. \nYou can register your requester using: registerRequester.py script."

    try:
        blockReadFrom, orcid = eBlocBroker.functions.getRequesterInfo(_requester).call()       
        event_filter = eBlocBroker.events.LogRequester.createFilter(fromBlock=int(blockReadFrom), toBlock=int(blockReadFrom) + 1)
        requesterInfo = {'requester':     _requester,
                         'blockReadFrom': blockReadFrom,
                         'email':         event_filter.get_all_entries()[0].args['email'],
                         'miniLockID':    event_filter.get_all_entries()[0].args['miniLockID'],
                         'ipfsAddress':   event_filter.get_all_entries()[0].args['ipfsAddress'],
                         'fID':           event_filter.get_all_entries()[0].args['fID'],
                         'orcid':         orcid,
                         'orcidVerify':   eBlocBroker.functions.isRequesterOrcIDVerified(_requester).call()}                 
        return True, requesterInfo
    except Exception:
        return False, traceback.format_exc()


if __name__ == '__main__': 
    if len(sys.argv) == 3:
        _requester = str(sys.argv[1])
        printType   = str(sys.argv[2])
    elif len(sys.argv) == 2:
        _requester = str(sys.argv[1])
        printType   = '0'        
    else:
        _requester = '0x57b60037b82154ec7149142c606ba024fbb0f991'
        printType  = '0'
        
    status, requesterInfo = getRequesterInfo(_requester)

    if status:
        print('{0: <15}'.format('requester: ')     + requesterInfo['requester'] + '\n' +
              '{0: <15}'.format('blockReadFrom: ') + str(requesterInfo['blockReadFrom']) + '\n' +
              '{0: <15}'.format('email: ')         + requesterInfo['email'] + '\n' +
              '{0: <15}'.format('miniLockID: ')    + requesterInfo['miniLockID'] + '\n' +
              '{0: <15}'.format('ipfsAddress: ')   + requesterInfo['ipfsAddress'] + '\n' +
              '{0: <15}'.format('fID: ')           + requesterInfo['fID'] + '\n' +
              '{0: <15}'.format('orcid: ')         + requesterInfo['orcid'] + '\n' + 
              '{0: <15}'.format('orcidVerify: ')   + str(requesterInfo['orcidVerify'])
        )
