#!/usr/bin/env python

from imports import *

array = eBlocBroker.functions.getClusterAddresses().call();

for i in range(0, len(array)): #{
    print(array[i])
#}
