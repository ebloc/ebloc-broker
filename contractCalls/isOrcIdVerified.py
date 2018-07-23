#!/usr/bin/env python

from imports import *

if __name__ == '__main__': #{
    if len(sys.argv) == 2:
        orcid = str(sys.argv[1]);
    else:
        orcid = "0000-0001-7642-0552";

    print(eBlocBroker.functions.isOrcIdVerified(orcid).call())
#}
