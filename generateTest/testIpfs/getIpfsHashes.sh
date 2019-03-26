#!/bin/bash

all=$(cat hashOutput.txt | awk '{print $1}')

mkdir -p ipfsHashes
cd ipfsHashes
for item in $all;
do
    ipfs get $item
done
cd ..
