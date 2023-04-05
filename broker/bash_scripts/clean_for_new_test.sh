#!/bin/bash

clean_gdrive () {
    echo "#> Running: ~/ebloc-broker/broker/python_scripts/clean_gdrive.py"
    for i in {1..2}; do ~/ebloc-broker/broker/python_scripts/clean_gdrive.py; done
    echo "[  OK  ]"
}

#if [[ "$EUID" -eq 0 ]]; then
#    echo "This script must be run as non-root. Please run without 'sudo'."
#    exit
#fi

# ~/personalize/bin/swap_space.sh >/dev/null 2>&1

# update block.continue.txt with the current block number
python3 -uB $HOME/ebloc-broker/broker/eblocbroker_scripts/get_block_number.py True
squeue | tail -n+2 | awk '{print $1}' | xargs scancel 2> /dev/null

# remove created users users
for user in $(members eblocbroker | tr " " "\n"); do
    echo $user will be deleted
    sudo userdel -f $user
done

BASE="/var/ebloc-broker"
if [[ -d $BASE ]]; then
    mkdir -p $BASE/to_delete

    mv $BASE/* $BASE/to_delete >/dev/null 2>&1
    DIR=$BASE/to_delete/public
    [ -d $DIR ] && mv $BASE/to_delete/public $BASE/

    DIR=$BASE/to_delete/cache  # do not delete files in /var/ebloc-broker/cache/
    [ -d $DIR ] && mv $DIR $BASE/

    FILE=$BASE/to_delete/slurm_mail_prog.sh # recover slurm_mail_prog.sh
    [ -f $FILE ] && mv $FILE $BASE/

    find /var/ebloc-broker/to_delete -name "*data_link*" | while read -r i
    do
        sudo umount -f $i/* >/dev/null 2>&1
    done
    sudo rm -rf $BASE/to_delete
    rm -f /var/ebloc-broker/cache/*.tar.gz
    mkdir -p $BASE/cache
fi

find $HOME/.ebloc-broker/*/* -mindepth 1 ! \
     -regex '^./private\(/.*\)?' -delete >/dev/null 2>&1

killall.sh

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

rm -f $HOME/.ebloc-broker/geth_server.out
rm -f $HOME/.ebloc-broker/.node-xmlhttprequest*
rm -f $HOME/.ebloc-broker/ipfs.out
rm -f $HOME/.ebloc-broker/modified_date.txt
rm -f $HOME/.ebloc-broker/package-lock.json

rm -rf ~/ebloc-broker/contract/build
rm -rf ~/ebloc-broker/contract/reports
rm -rf docs/_build_html/
rm -rf docs/_build/
rm -f /tmp/run/driver_popen.pid >/dev/null 2>&1
rm -f ~/.ebloc-broker/.oc_client.pckl
rm -f /var/ebloc-broker/cache/*.tar.gz


# unpin and remove all IPFS content from my machine
# ipfs pin ls --type recursive | cut -d' ' -f1 | ifne xargs -n1 ipfs pin rm
# ipfs repo gc
rm -rf ~/.ipfs/badgerds

clean_gdrive
for i in `gpg --list-keys --with-colons --fingerprint | sed -n 's/^fpr:::::::::\([[:alnum:]]\+\):/\1/p'`; do
    gpg --batch --delete-key "$i" 2>/dev/null
done

~/ebloc-broker/broker/libs/mongodb.py --delete-all

if [ "$(hostname)" = "homevm" ]; then
    echo "#> ln datasets for homevm"
    ~/ebloc-broker/broker/bash_scripts/ln_medium_data.sh
fi

if [[ -d $BASE ]]; then
    echo -e "\n/var/ebloc-broker/"
    CURRENT_DIR=$PWD
    cd /var/ebloc-broker && fdfind . | as-tree && cd ~
    cd $CURRENT_DIR
fi
