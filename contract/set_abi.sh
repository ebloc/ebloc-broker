#!/bin/bash

source $HOME/venv/bin/activate
input="$(cat <<EOF
import json
file = open("abi.json","w")
json.dump(eBlocBroker.abi, file)
file.close()
EOF
)"
echo "$input"
echo "$input" | brownie console --network bloxberg
mv abi.json $HOME/ebloc-broker/broker/eblocbroker_scripts/abi.json

printf "\n-------------------------\n"

input="$(cat <<EOF
import json
file = open("abi.json","w")
json.dump(USDTmy.abi, file)
file.close()
EOF
)"
echo "$input"
echo "$input" | brownie console --network bloxberg
mv abi.json $HOME/ebloc-broker/broker/eblocbroker_scripts/abi_usdtmy.json
