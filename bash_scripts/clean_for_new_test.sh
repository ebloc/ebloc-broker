#!/bin/bash
#                             |
# To Run: ./cleanForNewTest.sh|
#------------------------------

#if [[ "$EUID" -eq 0 ]]; then
#    echo "This script must be run as non-root. Please run without 'sudo'."
#    exit
#fi

rm -rf /var/eBlocBroker/*
mkdir -p /var/eBlocBroker/cache

find $HOME/.eBlocBroker/*/* -mindepth 1 ! -regex '^./private\(/.*\)?' -delete 2> /dev/null
rm -f $HOME/.eBlocBroker/my-app.pid
rm -f $HOME/.eBlocBroker/logJobs.txt
rm -f $HOME/.eBlocBroker/queuedJobs.txt
rm -f $HOME/.eBlocBroker/test.txt
rm -f $HOME/.eBlocBroker/ipfs.out

rm -f  $HOME/.eBlocBroker/endCodeAnalyse/*
rm -f  $HOME/.eBlocBroker/transactions/*

cat /dev/null > $HOME/.eBlocBroker/providerDriver.out

./killall.sh
clean.sh

python3 -uB $HOME/eBlocBroker/contractCalls/get_block_number.py True > $HOME/.eBlocBroker/blockReadFrom.txt
