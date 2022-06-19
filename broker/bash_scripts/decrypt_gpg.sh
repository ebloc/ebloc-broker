#!/bin/bash

for fn in */*; do
    echo "$fn"
    gpg --verbose --batch --yes --output=$(echo $fn | rev | cut -c5- | rev) --pinentry-mode loopback \
        --passphrase-file=~/.ebloc-broker/.gpg_pass.txt --decrypt "$fn"
done
rm */*.diff.gz.gpg
