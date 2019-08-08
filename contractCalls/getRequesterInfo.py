#!/usr/bin/env python3

import sys, os

def getRequesterInfo(_requester, printType, eBlocBroker=None, web3=None):
    if eBlocBroker is None and web3 is None:
        from imports import connectEblocBroker, getWeb3
        web3           = getWeb3()
        eBlocBroker    = connectEblocBroker(web3)
    
    _requester = web3.toChecksumAddress(_requester)
    
    if str(eBlocBroker.functions.isRequesterExists(_requester).call()) == "False":
        print("Requester is not registered. Please try again with registered Ethereum Address as requester. \nYou can register your requester using: registerRequester.py script.")
        sys.exit()
    
    blockReadFrom, orcid = eBlocBroker.functions.getRequesterInfo(_requester).call()       
    my_filter = eBlocBroker.eventFilter('LogRequester',{'fromBlock':int(blockReadFrom),'toBlock':int(blockReadFrom) + 1})
    
    if printType == '0':
        return('{0: <15}'.format('requester: ')     + _requester + '\n' +
               '{0: <15}'.format('blockReadFrom: ') + str(blockReadFrom) + '\n' +
               '{0: <15}'.format('email: ')         + my_filter.get_all_entries()[0].args['email'] + '\n' +
               '{0: <15}'.format('miniLockID: ')    + my_filter.get_all_entries()[0].args['miniLockID'] + '\n' +
               '{0: <15}'.format('ipfsAddress: ')   + my_filter.get_all_entries()[0].args['ipfsAddress'] + '\n' +
               '{0: <15}'.format('fID: ')           + my_filter.get_all_entries()[0].args['fID'] + '\n' +
               '{0: <15}'.format('orcid: ')         + orcid + '\n' + 
               '{0: <15}'.format('orcidVerify: ')   + str(eBlocBroker.functions.isRequesterOrcIDVerified(_requester).call()))
    else:
        return [str(blockReadFrom),
                my_filter.get_all_entries()[0].args['email'],
                my_filter.get_all_entries()[0].args['miniLockID'],
                my_filter.get_all_entries()[0].args['ipfsAddress'],
                my_filter.get_all_entries()[0].args['fID'],
                orcid,
                str(eBlocBroker.functions.isRequesterOrcIDVerified(_requester).call())]

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
        
    print(getRequesterInfo(_requester, printType))
