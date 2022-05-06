#!/bin/bash

for dir in */*; do
    gpg --verbose --batch --yes --output=$(echo $dir | rev | cut -c5- | rev) --pinentry-mode loopback --passphrase-file=/home/alper/.ebloc-broker/.gpg_pass.txt --decrypt "$dir"
done
rm */*.diff.gz.gpg
