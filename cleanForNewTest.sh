#!/bin/bash
#                             |
# To Run: ./cleanForNewTest.sh|
#------------------------------

if [[ "$EUID" -eq 0 ]]; then
    echo "This script must be run as non-root. Please run without 'sudo'."
    exit
fi

sudo rm -rf /var/eBlocBroker/*
mkdir /var/eBlocBroker/cache

sudo find $HOME/.eBlocBroker/*/* -mindepth 1 ! -regex '^./private\(/.*\)?' -delete
sudo rm -f  $HOME/.eBlocBroker/my-app.pid
sudo rm -f  $HOME/.eBlocBroker/checkSinfoOut.txt
sudo rm -f  $HOME/.eBlocBroker/logJobs.txt
sudo rm -f  $HOME/.eBlocBroker/queuedJobs.txt
sudo rm -f  $HOME/.eBlocBroker/test.txt
sudo rm -f  $HOME/.eBlocBroker/ipfs.out

cat /dev/null > $HOME/.eBlocBroker/clusterDriver.out

sudo ./killall.sh
sudo ./clean.sh

python3 -uB $HOME/eBlocBroker/contractCalls/blockNumber.py > $HOME/.eBlocBroker/blockReadFrom.txt
