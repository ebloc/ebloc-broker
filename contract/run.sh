#!/bin/bash

source $HOME/b/bin/activate

rm -f contracts/.\#Lib.sol
rm -f contracts/.\#Ownable.sol
rm -f contracts/.\#eBlocBroker.sol
rm -f contracts/.\#eBlocBrokerBase.sol
rm -f contracts/.\#eBlocBrokerInterface.sol
rm -f contracts/.\#eBlocBrokerInterface.sol
rm -f contracts/math/.\#SafeMath.sol

brownie compile
brownie test

rm -rf reports
