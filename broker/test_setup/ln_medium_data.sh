#!/bin/bash

cd /var/ebloc-broker/cache
# sudo umount -l
for fn in /mnt/hgfs/test_eblocbroker/medium/*; do
    fn=$(basename ${fn})
    mkdir -p $fn
    sudo mount --bind ~/test_eblocbroker/medium/$fn $fn
    sudo mount -o bind,remount,ro $fn
done
