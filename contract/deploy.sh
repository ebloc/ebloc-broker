#!/bin/bash

# network="eblocpoa"
network="bloxberg"
filename="eblocbroker_"$network"_deployed.txt"
echo -e "==> network="$network
rm -rf build/
brownie compile
brownie run eBlocBroker --network $network
echo -e "Setting ABI..."
./set_abi.sh  >/dev/null 2>&1
echo -e "done"
