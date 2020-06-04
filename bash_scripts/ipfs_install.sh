#!/bin/bash

# Install given version of IPFS. Check latest version from here: https://github.com/ipfs/go-ipfs/releases
# https://gist.github.com/MiguelBel/b3b5f711aa8d9362afa5f16e4e972461

# pre-requirements
sudo apt-get install golang-go -y



cd /tmp
version='v0.5.1'
                                           # go-ipfs_v0.5.1_linux-amd64.tar.gz
wget https://dist.ipfs.io/go-ipfs/${version}/go-ipfs_${version}_linux-386.tar.gz
tar -xvf go-ipfs_${version}_linux-386.tar.gz
sudo mv go-ipfs/ipfs /usr/local/bin/ipfs
rm go-ipfs_${version}_linux-386.tar.gz
rm -rf go-ipfs

echo ""
ipfs version
# ipfs version 0.5.1


# https://github.com/ipfs/ipfs-cluster
# https://cluster.ipfs.io/download/

cd /tmp
git clone https://github.com/ipfs/ipfs-cluster.git
cd ipfs-cluster
# export GO111MODULE=on # optional, if checking out the repository in $GOPATH.
go install ./cmd/ipfs-cluster-service
go install ./cmd/ipfs-cluster-ctl
go install ./cmd/ipfs-cluster-follow
