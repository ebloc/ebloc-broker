#!/usr/bin/env python

import sys

def isOrcIdVerified(orcID, eBlocBroker=None): #{
    if eBlocBroker is None: #{
        import os
        sys.path.insert(1, os.path.join(sys.path[0], '..'))
        from imports import connectEblocBroker
        eBlocBroker = connectEblocBroker()
    #}

    if eBlocBroker.functions.isOrcIdVerified(orcID).call() == 0:
        return 'False'
    else:
        return 'True'
#}
    
if __name__ == '__main__': #{
    if len(sys.argv) == 2:
        orcID = str(sys.argv[1]) 
    else:
        orcID = "0000-0001-7642-0552"
        
    print(isOrcIdVerified(orcID))
#}
