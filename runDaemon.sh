#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    nohup python -u Driver.py &
    sudo tail -f  nohup.out
else
    echo "This script must be run as non-root. Please run without 'sudo'." 
fi

