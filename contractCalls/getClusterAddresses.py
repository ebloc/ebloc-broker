#!/usr/bin/env python

import sys

def getClusterAddresses(eBlocBroker=None): #{
    if eBlocBroker is None: #{
        import os 
        sys.path.insert(1, os.path.join(sys.path[0], '..')) 
        from imports import connectEblocBroker
        eBlocBroker    = connectEblocBroker()
    #}
    return eBlocBroker.functions.getClusterAddresses().call() 
#}

if __name__ == '__main__': #{
    clusterList = getClusterAddresses()
    for i in range(0, len(clusterList)):
        print(clusterList[i])            
#}
