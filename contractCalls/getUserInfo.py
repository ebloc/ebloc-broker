#!/usr/bin/env python3

import sys, os

def getUserInfo(userAddress, printType, eBlocBroker=None, web3=None): #{
    if eBlocBroker is None and web3 is None:
        sys.path.insert(1, os.path.join(sys.path[0], '..'))
        from imports import connectEblocBroker
        from imports import getWeb3
        web3           = getWeb3()
        eBlocBroker    = connectEblocBroker(web3)
    
    userAddress = web3.toChecksumAddress(userAddress)
    
    if str(eBlocBroker.functions.isUserExist(userAddress).call()) == "False":
        print("User is not registered. Please try again with registered Ethereum Address as user. \nYou can register your user using: registerUser.py script.")
        sys.exit()
    
    blockReadFrom, orcid = eBlocBroker.functions.getUserInfo(userAddress).call()       
    my_filter = eBlocBroker.eventFilter('LogUser',{'fromBlock':int(blockReadFrom),'toBlock':int(blockReadFrom) + 1})
    
    if printType == '0':
        return('{0: <15}'.format('blockReadFrom: ') + str(blockReadFrom) + '\n' +
               '{0: <15}'.format('userEmail: ')     + my_filter.get_all_entries()[0].args['userEmail'] + '\n' +
               '{0: <15}'.format('miniLockID: ')    + my_filter.get_all_entries()[0].args['miniLockID'] + '\n' +
               '{0: <15}'.format('ipfsAddress: ')   + my_filter.get_all_entries()[0].args['ipfsAddress'] + '\n' +
               '{0: <15}'.format('fID: ')           + my_filter.get_all_entries()[0].args['fID'] + '\n' +
               '{0: <15}'.format('orcid: ')         + orcid + '.' + '\n' + 
               '{0: <15}'.format('orcidVerify: ')   + str(eBlocBroker.functions.isUserOrcIDVerified(userAddress).call()))
    else:
        return [str(blockReadFrom),
                my_filter.get_all_entries()[0].args['userEmail'],
                my_filter.get_all_entries()[0].args['miniLockID'],
                my_filter.get_all_entries()[0].args['ipfsAddress'],
                my_filter.get_all_entries()[0].args['fID'],
                orcid,
                str(eBlocBroker.functions.isUserOrcIDVerified(userAddress).call())]

if __name__ == '__main__': 
    if len(sys.argv) == 3:
        userAddress = str(sys.argv[1])
        printType   = str(sys.argv[2])
    else:
        userAddress = "0x4e4a0750350796164D8DefC442a712B7557BF282"
        printType   = '0'
        
    print(getUserInfo(userAddress, printType))
