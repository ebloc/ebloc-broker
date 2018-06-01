#!/bin/bash

export TESTRPC_GAS_LIMIT=8000000
py.test --capture=fd tests/test.py -s --disable-pytest-warnings
