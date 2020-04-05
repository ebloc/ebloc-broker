#!/bin/bash

# Parent hash of the most recent git commit that modified a file
echo 'eBlocBroker.sol'
hash_1=$(git log -n 1 --pretty=format:%H -- ../contract/contracts/eBlocBroker.sol)
git rev-list --parents -n 1 $hash_1

echo 'Lib.sol'
hash_2=$(git log -n 1 --pretty=format:%H -- ../contract/contracts/Lib.sol)
git rev-list --parents -n 1 $hash_2
