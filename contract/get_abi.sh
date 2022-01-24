#!/bin/bash

# source $HOME/v/bin/activate
cd ~/ebloc-broker/contract/
cat <<EOF | brownie console --network bloxberg
import json
with open('../broker/eblocbroker_scripts/abi.json','w') as fp:
    json.dump(eBlocBroker.abi, fp)
EOF
