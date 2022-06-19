#!/bin/bash

# run at requester-node
while read p; do
  ipfs get "$p"
done <result_ipfs_hashes.txt

mkdir -p ipfs
mv Qm* ipfs
cp -a ipfs ipfs_gpg
cd ipfs
rm */*.diff.gz.gpg
rmdir * >/dev/null 2>&1
cd ../ipfs_gpg
rm */*.diff.gz
rmdir * >/dev/null 2>&1
cd ..

cd ipfs_gpg
for fn in */*; do
    echo "$fn"
    gpg --verbose --batch --yes --output=$(echo $fn | rev | cut -c5- | rev) --pinentry-mode loopback \
        --passphrase-file=~/.ebloc-broker/.gpg_pass.txt --decrypt "$fn"
done
rm */*.diff.gz.gpg
cd ..
