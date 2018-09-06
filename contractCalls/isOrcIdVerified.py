#!/usr/bin/env python

from imports import *

if __name__ == '__main__': #{
    if len(sys.argv) == 2:
        orcID = str(sys.argv[1]) 
    else:
        orcID = "0000-0001-7642-0552" 
        
    if eBlocBroker.functions.isOrcIdVerified(orcID).call() == 0:
        print('False') 
    else:
        print('True') 
#}
