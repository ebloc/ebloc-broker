#!/bin/bash

IPFS_PATH="/home/whoami/.ipfs"
export IPFS_PATH
ipfsHash=$1 
ipfs get $ipfsHash --output=$2
