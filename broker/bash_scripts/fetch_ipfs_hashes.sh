#!/bin/bash

while read p; do
  ipfs get "$p"
done <result_ipfs_hashes.txt

mkdir -p ipfs
mv Qm* ipfs
cp -a ipfs ipfs_gpg
cd ipfs
rm */*.diff.gz.gpg
rmdir *
cd ../ipfs_gpg
rm */*.diff.gz
rmdir *
cd ..
