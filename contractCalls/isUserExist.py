#!/usr/bin/env python

from imports import *

if __name__ == '__main__': #{    
    if(len(sys.argv) == 2):
        userAddress = str(sys.argv[1]);
    else:
        userAddress = "0x4e4a0750350796164d8defc442a712b7557bf282"; #POA
        # userAddress = "0x8642AF57Dc56d577276B5D6Bdb123ece429f093b"; #POW
        
    userAddress = web3.toChecksumAddress(userAddress);
    print(str(eBlocBroker.functions.isUserExist(userAddress).call()).rstrip('\n'));
#}
