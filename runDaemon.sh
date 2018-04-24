#!/bin/bash

# source $HOME/.venv-py3/bin/activate
. venv/bin/activate

# gopath=$(go env | grep 'GOPATH' | cut -d "=" -f 2 | tr -d '"');
# export PATH=$PATH:$gopath/bin;

if [[ $EUID -ne 0 ]]; then
    nohup python -Bu Driver.py > clusterDriver.out 2>&1 &
    sudo tail -f  clusterDriver.out
else
    echo "This script must be run as non-root. Please run without 'sudo'." 
fi

