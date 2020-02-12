#!/bin/bash

source $HOME/venv/bin/activate
brownie compile

pytest tests -x -s
# pytest tests -s -x -k "test_workflow"
