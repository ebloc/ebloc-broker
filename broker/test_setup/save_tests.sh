#!/bin/bash

mkdir -p ~/TESTS
cd ~/TESTS
cp -a ~/.ebloc-broker ~/TESTS/ebloc-broker
cd ~/TESTS/ebloc-broker
rm .bloxberg_account.yaml
rm .*lock
rm .oc_client.pckl
rm .gpg_pass.txt
rm .eudat_client.txt
rm -rf links
rm -rf private
rmdir *
cd ~/TESTS
tar -cvf ebb.tar.gz ebloc-broker
rm -rf ebloc-broker
