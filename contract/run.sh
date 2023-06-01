#!/bin/bash

TEST_ALL=1
source $HOME/venv/bin/activate
echo -n "brownie compile "
brownie compile >/dev/null 2>&1
echo "done"
$HOME/ebloc-broker/broker/_daemons/ganache.py 8547
# pytest tests --capture=sys -s -x -k "test_multiple_data" --disable-pytest-warnings
# pytest tests --capture=sys -s -x -k " test_data_info" --disable-pytest-warnings
# pytest tests/test_overlap.py -s -x -v --disable-pytest-warnings --log-level=INFO  # test all
# pytest tests --capture=sys -s -x -k "test_update_provider" --disable-pytest-warnings
# -I
# -s -v  // verbose
# pytest tests --capture=sys -s -x -k "test_test3" --disable-pytest-warnings
if [ $TEST_ALL -eq 1 ]; then
    pytest tests -s -x --disable-pytest-warnings --log-level=INFO -v --tb=line # tests all cases
else  #: gives priority
    pytest tests --capture=sys -s -x -k "test_workflow" --disable-pytest-warnings -vv --tb=line
    # pytest tests --capture=sys -s -x -k " test_simple_submit" --disable-pytest-warnings -v --tb=line
    # pytest tests --capture=sys -s -x -k "test_overall_eblocbroker" --disable-pytest-warnings -v --tb=line
    # pytest tests --capture=sys -s -x -k "test_transfer" --disable-pytest-warnings -v --tb=line
    # pytest tests --capture=sys -s -x -k "test_receive_registered_data_deposit" --disable-pytest-warnings -v --tb=line
fi
rm -rf reports/
