#!/bin/bash

# Force my local master to be origin/maste
git checkout master
git reset --hard origin/master

git fetch --all
git checkout origin/master -- $HOME/eBlocBroker/contract/
git checkout origin/master -- $HOME/eBlocBroker/eblocbroker/contract.json
git checkout origin/master -- $HOME/eBlocBroker/eblocbroker/abi.json
