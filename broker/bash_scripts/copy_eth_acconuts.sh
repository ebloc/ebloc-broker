#!/bin/bash

sudo chown alper -R /home/alper/.eblocpoa/keystore/
cp /home/alper/.eblocpoa/keystore/* /home/alper/.brownie/accounts
sudo chown alper -R ~/.brownie/accounts/*
cd ~/.brownie/accounts/
for f in *; do
    if [[ $f != *.json ]]; then
        # Convert "." into "_"
        rename -vf "s/\./_/g" "$f"
    fi
done

for f in *; do
    if [[ $f != *.json ]]; then
        # Add ".json" at the end
        mv -f "$f" "$f.json";
    fi
done

tar -zcf ~/.share/accounts.tar.gz *
