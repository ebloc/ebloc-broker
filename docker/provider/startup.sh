#!/bin/bash

echo "" && date "+%a %e %b %Y %H:%M:%S %Z"
cd /workspace/ebloc-broker
git fetch --all --quiet
git submodule update --init
git submodule update --quiet
git pull --all -r -v
