#!/bin/bash

source $HOME/v/bin/activate
brownie compile
pytest tests -s -x --capture=no 
# pytest tests -s -x --capture=no -k "test_storageRefund"
