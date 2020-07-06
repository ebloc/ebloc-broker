#!/bin/bash

# jq-doc: https://stackoverflow.com/a/24943373/2402577

source $HOME/venv/bin/activate
brownie compile
brownie run eBlocBroker --network private | tee eblocbroker_deployed.txt

file=$HOME/eBlocBroker/eblocbroker/contract.json

ebb_tx=$(grep "Transaction sent:" eblocbroker_deployed.txt | sed 's/^.*: //' | tail -n 1)
ebb_address=$(grep "eBlocBroker deployed at:" eblocbroker_deployed.txt  | sed 's/^.*: //')

remove_ansi_escape_sequence="$(cat <<EOF
#!/usr/bin/env python3
import subprocess
import re

ebb_tx = subprocess.check_output (["echo","$ebb_tx"]).strip().decode("utf-8")
ebb_address = subprocess.check_output (["echo","$ebb_address"]).strip().decode("utf-8")

ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
print(ansi_escape.sub("", ebb_tx) + " " + ansi_escape.sub("", ebb_address))
EOF
)"

output=$(echo "$remove_ansi_escape_sequence" | python3)
output=($output)
ebb_tx=${output[0]}
ebb_address=${output[1]}

# sed -i 's/\\\u001b\[0\;1\;34m//g' $file
# sed -i 's/\\\u001b\[0\;m//g' $file

jq '.txHash = $newVal' --arg newVal $ebb_tx $file > tmp.$$.json && mv tmp.$$.json $file
jq '.address = $newVal' --arg newVal $ebb_address $file > tmp.$$.json && mv tmp.$$.json $file
cat $file

printf "Setting abi"
./set_abi.sh
