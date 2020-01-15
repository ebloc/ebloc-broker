#!/bin/bash

source $HOME/v/bin/activate

cat <<EOF | brownie console --network private
import json
with open('abi.json','w') as fp: json.dump(eBlocBroker.abi, fp)
EOF
