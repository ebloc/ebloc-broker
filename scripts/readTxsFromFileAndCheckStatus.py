#!/usr/bin/env python3

import sys, os
import lib
from imports import getWeb3

web3 = getWeb3()

with open("dum.txt") as f:
    lines = f.read().splitlines()

for i in range(0, len(lines)):
    tx = lines[i]
    res = lib.isTransactionPassed(web3, tx)
    if not res:
        print(tx + " " + str(res))
