#!/bin/bash

#if [[ "$EUID" -eq 0 ]]; then
#    echo "This script must be run as non-root. Please run without 'sudo'."
#    exit
#fi

base="/var/eBlocBroker"
mkdir -p $base/to_delete

mv $base/* $base/to_delete 2>/dev/null

if [ -d "$base/to_delete/public" ]; then
    mv $base/to_delete/public $base/
fi

rm -rf $base/to_delete
mkdir -p $base/cache

find $HOME/.eBlocBroker/*/* -mindepth 1 ! \
     -regex '^./private\(/.*\)?' -delete 2> /dev/null

rm -f $HOME/.eBlocBroker/end_code_output/*
rm -f $HOME/.eBlocBroker/transactions/*
rm -f $HOME/.eBlocBroker/drivers_output/*
rm -f $HOME/.eBlocBroker/my-app.pid

cat /dev/null > $HOME/.eBlocBroker/provider.log
cat /dev/null > $HOME/.eBlocBroker/log.txt

killall.sh

rm -f $base/geth_server.out
rm -f $base/.node-xmlhttprequest*
rm -f $base/ipfs.out
rm -f $base/modified_date.txt
rm -f $base/package-lock.json
# rm -f .oc.pckl
rm -f $HOME/eBlocBroker/base/meta_data.json

rm -rf docs/_build_html/
rm -rf docs/_build/

cp $HOME/eBlocBroker/bash_scripts/slurmScript.sh $base
# Update block.continue.txt with the current block number
python3 -uB $HOME/eBlocBroker/eblocbroker/get_block_number.py True > \
        $HOME/.eBlocBroker/block_continue.txt

# python3 $HOME/eBlocBroker/mongodb/delete_all.py
