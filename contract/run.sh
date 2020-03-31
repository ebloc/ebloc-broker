#!/bin/bash

source $HOME/venv/bin/activate
which brownie
brownie compile

pytest tests -x -s
# pytest tests -s -x -k "test_stored_data_usage"
