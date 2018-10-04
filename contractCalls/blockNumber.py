#!/usr/bin/env python3

def blockNumber(web3=None): #{
    if web3 != None:
        return str(web3.eth.blockNumber).replace("\n", "")
    else:
        import sys, os 
        sys.path.insert(1, os.path.join(sys.path[0], '..')) 
        from imports import getWeb3
        
        web3 = getWeb3() 
        return str(web3.eth.blockNumber).replace("\n", "") 
#}

if __name__ == '__main__': #{
    print(blockNumber())
#}
