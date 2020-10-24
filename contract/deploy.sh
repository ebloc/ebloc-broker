#!/bin/bash

rm -rf build/
brownie compile
brownie run eBlocBroker --network eblocpoa | tee eblocbroker_deployed.txt
