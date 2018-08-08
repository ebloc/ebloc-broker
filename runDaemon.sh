#!/bin/bash                      
#                         |
# To Run:  ./runDaemon.sh |
#--------------------------

sudo printf ''

if [[ "$EUID" -ne 0 ]]; then
    . venv/bin/activate;
    nohup python -Bu Driver.py >> $HOME/.eBlocBroker/clusterDriver.out 2>&1 &
    sudo tail -f $HOME/.eBlocBroker/clusterDriver.out
else
    echo "This script must be run as non-root. Please run without 'sudo'." 
fi

#gopath=$(go env | grep 'GOPATH' | cut -d "=" -f 2 | tr -d '"');
#export PATH=$PATH:$gopath/bin;

# sudo su -c ". venv/bin/activate && nohup python -Bu Driver.py >> $HOME/.eBlocBroker/clusterDriver.out 2>&1 &"
# sudo tail -f $HOME/.eBlocBroker/clusterDriver.out
