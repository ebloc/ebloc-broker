#!/bin/bash

source $HOME/venv/bin/activate

input="$(cat <<EOF
import json
file = open("abi.json","w")
json.dump(eBlocBroker.abi, file)
file.close()
EOF
)"

echo "$input" | brownie console --network private
mv abi.json $HOME/eBlocBroker/eblocbroker/abi.json
