#!/bin/bash

#if [[ "$EUID" -eq 0 ]]; then
#    echo "This script must be run as non-root. Please run without 'sudo'."
#    exit
#fi

base="/var/eBlocBroker"
mkdir -p $base/to_delete
mv $base/* $base/to_delete 2>/dev/null
mv $base/to_delete/public $base/
rm -rf $base/to_delete
mkdir -p $base/cache

find $HOME/.eBlocBroker/*/* -mindepth 1 ! -regex '^./private\(/.*\)?' -delete 2> /dev/null
rm -f $HOME/.eBlocBroker/my-app.pid
rm -f $HOME/.eBlocBroker/logJobs.txt
rm -f $HOME/.eBlocBroker/queuedJobs.txt
rm -f $HOME/.eBlocBroker/test.txt
rm -f $HOME/.eBlocBroker/ipfs.out

rm -f  $HOME/.eBlocBroker/endCodeAnalyse/*
rm -f  $HOME/.eBlocBroker/transactions/*

cat /dev/null > $HOME/.eBlocBroker/provider.log

./killall.sh
clean.sh

# Update block.continue.txt with the current block number
python3 -uB $HOME/eBlocBroker/eblocbroker/get_block_number.py True > $HOME/.eBlocBroker/block_continue.txt
