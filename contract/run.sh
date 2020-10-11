#!/bin/bash

source $HOME/venv/bin/activate
brownie compile

PORT=8547
sed -i 's/\(port: \).*/\1'$PORT'/' ~/.brownie/network-config.yaml

$HOME/eBlocBroker/daemons/ganache.py $PORT

# pytest tests -s -x -v --disable-pytest-warnings --log-level=INFO  # test all
pytest tests --capture=sys -s -x -k "test_submitJob_gas" --disable-pytest-warnings

# -I
# -s -v  // verbose
# pytest tests -s -x -k "test_register" --disable-pytest-warnings
