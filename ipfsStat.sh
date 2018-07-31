#!/bin/bash

IPFS_PATH=$HOME"/.ipfs"
export IPFS_PATH
ipfsHash=$1 
timeout 300 ipfs object stat $ipfsHash #Wait 5 minutes. 
