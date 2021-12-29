#!/bin/bash

#if [[ "$EUID" -eq 0 ]]; then
#    echo "This script must be run as non-root. Please run without 'sudo'."
#    exit
#fi

# update block.continue.txt with the current block number
python3 -uB $HOME/ebloc-broker/broker/eblocbroker_scripts/get_block_number.py True

# remove created users users
for user in $(members eblocbroker | tr " " "\n")
do
    echo $user will be deleted
    sudo userdel -f $user
done

base="/var/ebloc-broker"
mkdir -p $base/to_delete

mv $base/* $base/to_delete 2>/dev/null
DIR=$base/to_delete/public
[ -d $DIR ] && mv $base/to_delete/public $base/

DIR=$base/to_delete/cache  # do not delete files in /var/ebloc-broker/cache/
[ -d $DIR ] && mv $DIR $base/

FILE=$base/to_delete/slurm_mail_prog.sh # recover slurm_mail_prog.sh
[ -f $FILE ] && mv $FILE $base/

find /var/ebloc-broker/to_delete -name "*data_link*" | while read -r i
do
    sudo umount -f $i/*
done
sudo rm -rf $base/to_delete
rm -f /var/ebloc-broker/cache/*.tar.gz
mkdir -p $base/cache
find $HOME/.ebloc-broker/*/* -mindepth 1 ! \
     -regex '^./private\(/.*\)?' -delete 2> /dev/null

rm -rf $HOME/.ebloc-broker/transactions/*
rm -f $HOME/.ebloc-broker/end_code_output/*
rm -f $HOME/.ebloc-broker/drivers_output/*
rm -f $HOME/.ebloc-broker/my-app.pid
rm -f $HOME/.ebloc-broker/test.log

cat /dev/null > $HOME/.ebloc-broker/provider.log
rm -f $HOME/.ebloc-broker/log.txt
rm -f $HOME/.ebloc-broker/test.log
rm -f $HOME/.ebloc-broker/watch_0x*.out
rm -f $HOME/.ebloc-broker/ipfs.out
rm -f $HOME/.ebloc-broker/ganache.out
rm -f $HOME/.ebloc-broker/*.yaml~

killall.sh

rm -f $base/geth_server.out
rm -f $base/.node-xmlhttprequest*
rm -f $base/ipfs.out
rm -f $base/modified_date.txt
rm -f $base/package-lock.json
# rm -f .oc.pckl
rm -rf docs/_build_html/
rm -rf docs/_build/
rm /tmp/run/driver_popen.pid
rm -f ~/.ebloc-broker/.oc_client.pckl

# unpin and remove all IPFS content from my machine
ipfs pin ls --type recursive | cut -d' ' -f1 | ifne xargs -n1 ipfs pin rm
ipfs repo gc

$HOME/ebloc-broker/broker/libs/mongodb.py --delete-all

echo -e "\n$ ls /var/ebloc-broker"
ls /var/ebloc-broker/

# command rm -rf ~/.local/share/Trash/files/*
