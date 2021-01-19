#!/bin/bash

rm -rf build/
brownie compile
brownie run eBlocBroker --network eblocpoa | \
    tee |  sed 's/\x1B\[[0-9;]\{1,\}[A-Za-z]//g' > eblocbroker_deployed.txt
cat eblocbroker_deployed.txt
