#!/usr/bin/env python

from imports import *

if __name__ == '__main__': #{
    account            = web3.eth.accounts[0];
    # USER Inputs----------------------------------------------------------------
    if len(sys.argv) == 2:
        orcID = str(sys.argv[1]);
    else:
        orcID = "0000-0001-7642-0552";
    # ----------------------------------------------------------------------------

    
    if eBlocBroker.functions.isOrcIdVerified(orcID).call() == 0:
        tx = eBlocBroker.transact({"from":account, "gas": 4500000}).authenticateORCID(orcID);
        print('Tx: ' + tx.hex());
    else:
        print('OrcID: ' + orcID + ' is already authenticated.')
#}
