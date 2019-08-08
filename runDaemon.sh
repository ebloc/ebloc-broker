#!/bin/bash                      
#                         |
# To Run:  ./runDaemon.sh |
#--------------------------

sudo printf ''

if [[ "$EUID" -ne 0 ]]; then
    # source $HOME/venv/bin/activate
    nohup python3 -Bu Driver.py >> $HOME/.eBlocBroker/providerDriver.out 2>&1 &
    tail -f $HOME/.eBlocBroker/providerDriver.out
else
    echo "This script must be run as non-root. Please run without 'sudo'." 
fi

#gopath=$(go env | grep 'GOPATH' | cut -d "=" -f 2 | tr -d '"');
#export PATH=$PATH:$gopath/bin;
