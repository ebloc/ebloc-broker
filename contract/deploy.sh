#!/bin/bash

source $HOME/venv/bin/activate
brownie compile
brownie run eBlocBroker --network private
