#!/bin/bash

source $HOME/venv/bin/activate

input="$(cat <<EOF
import json
file = open("abi.json","w")
json.dump(eBlocBroker.abi, file)
file.close()
EOF
)"

printf "Setting ABI\n"

echo "$input"
echo "$input" | brownie console --network eblocpoa
mv abi.json $HOME/eBlocBroker/eblocbroker/abi.json
