#!/bin/bash

source $HOME/venv/bin/activate

rm -rf reports/
brownie compile

brownie compile
PORT=8547
$HOME/eBlocBroker/daemons/ganache.py $PORT

pytest tests -s -x -v --disable-pytest-warnings --log-level=INFO  # test all
# pytest tests --capture=sys -s -x -k "test_submitJob_gas" --disable-pytest-warnings
# pytest tests --capture=sys -s -x -k "test_submit_job" --disable-pytest-warnings

# -I
# -s -v  // verbose
rm -rf reports/
