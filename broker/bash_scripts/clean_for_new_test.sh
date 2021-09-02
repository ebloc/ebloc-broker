#!/bin/bash

#if [[ "$EUID" -eq 0 ]]; then
#    echo "This script must be run as non-root. Please run without 'sudo'."
#    exit
#fi

# Update block.continue.txt with the current block number
python3 -uB $HOME/ebloc-broker/broker/eblocbroker/get_block_number.py True

base="/var/ebloc-broker"
mkdir -p $base/to_delete

mv $base/* $base/to_delete 2>/dev/null

if [ -d "$base/to_delete/public" ]; then
    mv $base/to_delete/public $base/
fi

rm -rf $base/to_delete
mkdir -p $base/cache

find $HOME/.ebloc-broker/*/* -mindepth 1 ! \
     -regex '^./private\(/.*\)?' -delete 2> /dev/null

rm -f $HOME/.ebloc-broker/end_code_output/*
rm -f $HOME/.ebloc-broker/transactions/*
rm -f $HOME/.ebloc-broker/drivers_output/*
rm -f $HOME/.ebloc-broker/my-app.pid

cat /dev/null > $HOME/.ebloc-broker/provider.log
cat /dev/null > $HOME/.ebloc-broker/log.txt

killall.sh

rm -f $base/geth_server.out
rm -f $base/.node-xmlhttprequest*
rm -f $base/ipfs.out
rm -f $base/modified_date.txt
rm -f $base/package-lock.json
# rm -f .oc.pckl

rm -rf docs/_build_html/
rm -rf docs/_build/

cp $HOME/ebloc-broker/broker/bash_scripts/slurmScript.sh $base
$HOME/ebloc-broker/broker/libs/mongodb.py --delete-all
