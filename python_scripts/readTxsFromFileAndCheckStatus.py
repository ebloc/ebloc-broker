#!/usr/bin/env python3

from imports import connect_to_web3
from utils import is_transaction_passed

web3 = connect_to_web3()

with open("dum.txt") as f:
    lines = f.read().splitlines()

for i in range(0, len(lines)):
    tx = lines[i]
    output = is_transaction_passed(web3, tx)
    if not output:
        print(tx + " " + str(output))
