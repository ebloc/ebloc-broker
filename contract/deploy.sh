#!/bin/bash

# jq-doc: https://stackoverflow.com/a/24943373/2402577

source $HOME/venv/bin/activate
brownie compile
brownie run eBlocBroker --network private | tee eblocbroker_deployed.txt

file=$HOME/eBlocBroker/eblocbroker/contract.json

# Seting tx_hash
ebb_tx=$(grep "Transaction sent:" eblocbroker_deployed.txt | sed 's/^.*: //' | tail -n 1)
jq '.txHash = $newVal' --arg newVal $ebb_tx $file > tmp.$$.json && mv tmp.$$.json $file

# Seting tx_address
ebb_address=$(grep "eBlocBroker deployed at:" eblocbroker_deployed.txt  | sed 's/^.*: //')
jq '.address = $newVal' --arg newVal $ebb_address $file > tmp.$$.json && mv tmp.$$.json $file

sed -i 's/\\\u001b\[0\;1\;34m//g' $file
sed -i 's/\\\u001b\[0\;m//g' $file

cat $file

printf "Setting abi"
./set_abi.sh
