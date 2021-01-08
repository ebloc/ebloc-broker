#!/bin/bash

# NETWORK="eblocpoa"
NETWORK="bloxberg"
filename="eblocbroker_"$NETWORK"_deployed.txt"
# rm -rf build/
brownie compile
brownie run eBlocBroker --network $NETWORK | \
    tee |  sed 's/\x1B\[[0-9;]\{1,\}[A-Za-z]//g' > $filename
cat $filename
