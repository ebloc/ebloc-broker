#!/bin/bash

~/personalize/bin/mount_ebb.sh
# linking large folders from disk in homevm machine
cd /var/ebloc-broker/cache
sudo umount -l /var/ebloc-broker/cache/* >/dev/null 2>&1
for fn in /mnt/hgfs/test_eblocbroker/medium/*; do
    fn=$(basename ${fn})
    mkdir -p $fn >/dev/null 2>&1
    sudo mount --bind ~/test_eblocbroker/medium/$fn $fn
    sudo mount -o bind,remount,ro $fn
done
ls /var/ebloc-broker/cache/0d6c3288ef71d89fb93734972d4eb903
