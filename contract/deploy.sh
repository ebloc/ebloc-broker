#!/bin/bash

# network="eblocpoa"
network="bloxberg"
echo -e "==> network="$network
rm -rf build/
brownie compile
brownie run eBlocBroker --network $network
printf "## Setting ABI...  "
./set_abi.sh  >/dev/null 2>&1
echo "[  OK  ]"
