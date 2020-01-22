#!/bin/bash

source $HOME/venv/bin/activate
brownie compile

pytest tests -s -x --capture=no
# pytest tests -s -x --capture=no -k "test_workflow"
