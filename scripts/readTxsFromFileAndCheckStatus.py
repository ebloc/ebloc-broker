#!/usr/bin/env python3

import os
import sys

import lib
from imports import connect_to_web3

web3 = connect_to_web3()

with open("dum.txt") as f:
    lines = f.read().splitlines()

for i in range(0, len(lines)):
    tx = lines[i]
    res = lib.is_transaction_passed(web3, tx)
    if not res:
        print(tx + " " + str(res))
