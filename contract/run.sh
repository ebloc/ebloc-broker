#!/bin/bash

rm contracts/.\#eBlocBroker.sol
rm contracts/.\#Lib.sol
brownie compile
brownie test
