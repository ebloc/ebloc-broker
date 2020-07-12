#!/bin/bash

brownie compile
brownie run eBlocBroker --network private | tee eblocbroker_deployed.txt
