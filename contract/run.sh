#!/bin/bash

TEST_ALL=1
source $HOME/venv/bin/activate
brownie compile
$HOME/ebloc-broker/broker/_daemons/ganache.py 8547
# pytest tests --capture=sys -s -x -k "test_multiple_data" --disable-pytest-warnings
# pytest tests --capture=sys -s -x -k " test_data_info" --disable-pytest-warnings
# pytest tests/test_overlap.py -s -x -v --disable-pytest-warnings --log-level=INFO  # test all
# pytest tests --capture=sys -s -x -k "test_update_provider" --disable-pytest-warnings
# -I
# -s -v  // verbose
# pytest tests --capture=sys -s -x -k "test_submit_job" --disable-pytest-warnings
# pytest tests --capture=sys -s -x -k "test_test3" --disable-pytest-warnings
if [ $TEST_ALL -eq 1 ]; then
    pytest tests -s -x -vv --disable-pytest-warnings --log-level=INFO  # tests all cases
else
    pytest tests --capture=sys -s -x -k "test_receive_registered_data_deposit" --disable-pytest-warnings
fi
rm -rf reports/
