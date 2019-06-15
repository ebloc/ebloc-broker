#!/bin/bash

source $HOME/b/bin/activate

rm contracts/.\#eBlocBroker.sol
rm contracts/.\#Lib.sol

# pid=$(sudo lsof -n -i :8545 | grep LISTEN| awk '{print $2}');
# if [ -n "$pid" ]; then
#   sudo kill -9 $pid 
# fi

brownie compile
brownie test
