#!/usr/bin/env python

from imports import *

if __name__ == '__main__': #{
    if len(sys.argv) == 3:
        userAddress = str(sys.argv[1]);
        printType   = str(sys.argv[2]);
    else:
        userAddress = "0x82f0d257a9832fa1381881b8dce2d2e6aebc8251";
        printType   = '0';

    userAddress = web3.toChecksumAddress(userAddress);
    
    if (str(eBlocBroker.functions.isUserExist(userAddress).call()) == "False"): #{
        print("User is not registered. Please try again with registered Ethereum Address as user. \nYou can register your user using: registerUser.py script.")
        sys.exit();
    #}
    
    blockReadFrom, orcid = eBlocBroker.functions.getUserInfo(userAddress).call();       
    my_filter = eBlocBroker.eventFilter('LogUser',{'fromBlock':int(blockReadFrom),'toBlock':int(blockReadFrom) + 1})
    
    if printType == '0': #{
        print('{0: <17}'.format('blockReadFrom: ') + str(blockReadFrom))    
        print('{0: <17}'.format('userEmail: ')     + my_filter.get_all_entries()[0].args['userEmail'])
        print('{0: <17}'.format('miniLockID: ')    + my_filter.get_all_entries()[0].args['miniLockID'])
        print('{0: <17}'.format('ipfsAddress: ')   + my_filter.get_all_entries()[0].args['ipfsAddress'])   
        print('{0: <17}'.format('fID: ')           + my_filter.get_all_entries()[0].args['fID'])
        print('{0: <17}'.format('orcid: ')         + orcid)        
        print('{0: <17}'.format('orcidVerify: ')   + str(eBlocBroker.functions.isOrcIdVerified(orcid).call()))
    #}
    else: #{
        print(str(blockReadFrom) + ',' +
              my_filter.get_all_entries()[0].args['userEmail']   + ',' +
              my_filter.get_all_entries()[0].args['miniLockID']  + ',' +
              my_filter.get_all_entries()[0].args['ipfsAddress'] + ',' +
              my_filter.get_all_entries()[0].args['fID']         + ',' +
              orcid                                              + ',' +
              str(eBlocBroker.functions.isOrcIdVerified(orcid).call())
        );
    #}
#}
