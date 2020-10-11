#!/bin/bash

brownie compile
brownie run eBlocBroker --network eblocpoa | tee eblocbroker_deployed.txt
