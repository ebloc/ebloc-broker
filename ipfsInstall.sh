#!/bin/bash

# Install given version of IPFS. Check latest version from here: https://github.com/ipfs/go-ipfs/releases
# https://gist.github.com/MiguelBel/b3b5f711aa8d9362afa5f16e4e972461

version='v0.4.17'
sudo apt-get install golang-go -y
wget https://dist.ipfs.io/go-ipfs/${version}/go-ipfs_${version}_linux-386.tar.gz
tar xvfz go-ipfs_${version}_linux-386.tar.gz
sudo mv go-ipfs/ipfs /usr/local/bin/ipfs
rm go-ipfs_${version}_linux-386.tar.gz
rm -rf go-ipfs/

echo ''
ipfs version
