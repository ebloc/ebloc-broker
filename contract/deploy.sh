#!/bin/bash

# ./deploy.sh | tee deploy_output.tex

network="bloxberg"  # "eblocpoa"
echo -e "## network="$network
rm -rf build/
brownie compile
brownie run eBlocBroker --network $network
printf "## setting abi... "
./set_abi.sh  >/dev/null 2>&1
echo "done"
