#!/bin/bash

source $HOME/venv/bin/activate
which brownie
brownie compile

$HOME/eBlocBroker/daemons/ganache.py

# pytest tests -x -s --disable-pytest-warnings --log-level=INFO
pytest tests -s -x -k "test_update_provider" --disable-pytest-warnings
