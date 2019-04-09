#!/bin/bash

# brew switch solidity 0.4.17

source $HOME/myapp/bin/activate
rm -rf tests/__pycache__
export TESTRPC_GAS_LIMIT=8000000
py.test --capture=fd tests/test.py -s --disable-pytest-warnings
