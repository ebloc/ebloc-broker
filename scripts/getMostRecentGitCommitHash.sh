#!/bin/bash

cd ../
# Parent hash of the most recent git commit that modified a file (address.json)
hash=$(git log -n 1 --pretty=format:%H -- contractCalls/address.json)
git rev-list --parents -n 1 $hash
