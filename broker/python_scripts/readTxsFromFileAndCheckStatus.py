#!/usr/bin/env python3

from broker.utils import is_transaction_passed


with open("dum.txt") as f:
    lines = f.read().splitlines()

for tx in lines:
    output = is_transaction_passed(tx)
    if not output:
        print(tx + " " + str(output))
