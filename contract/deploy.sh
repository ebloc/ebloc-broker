#!/bin/bash

source $HOME/v/bin/activate
brownie compile
brownie run eBlocBroker --network private
