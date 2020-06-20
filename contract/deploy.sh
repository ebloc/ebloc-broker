#!/bin/bash

source $HOME/venv/bin/activate
brownie compile
brownie run eBlocBroker --network private | tee eblocbroker_deployed.txt

./set_abi.sh
