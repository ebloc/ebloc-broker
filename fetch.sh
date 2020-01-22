#!/bin/bash

git fetch
git checkout origin/master -- contract/
git checkout origin/master -- contractCalls/contract.json
git checkout origin/master -- contractCalls/abi.json
