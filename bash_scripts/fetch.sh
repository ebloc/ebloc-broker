#!/bin/bash

# Force my local master to be origin/maste
git checkout master
git reset --hard origin/master

git fetch
git checkout origin/master -- contract/
git checkout origin/master -- contractCalls/contract.json
git checkout origin/master -- contractCalls/abi.json
