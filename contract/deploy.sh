#!/bin/bash

# network="eblocpoa"
network="bloxberg"
filename="eblocbroker_"$network"_deployed.txt"
echo -e "==> network="$network
rm -rf build/
brownie compile
brownie run eBlocBroker --network $network
#     | \
#     tee |  sed 's/\x1B\[[0-9;]\{1,\}[A-Za-z]//g' > $filename
# cat $filename
