#!/bin/bash

# Install IPFS

# Download the Linux binary from dist.ipfs.io (opens new window).

# Install given version of IPFS. Check latest version from here: https://github.com/ipfs/go-ipfs/releases
# https://gist.github.com/MiguelBel/b3b5f711aa8d9362afa5f16e4e972461

# For macOS: `brew upgrade ipfs`

# pre-requirements
sudo apt-get install golang-go -y

ipfs_current_version=$(ipfs version | awk '{ print $3 }')
cd /tmp
# version=$(curl -s https://github.com/ipfs/go-ipfs/releases/latest | grep -oP 'Release v\K.*?(?= )' | head -n1)
version="0.7.0"

echo "version to download=v"$version
                                            # go-ipfs_${version}_linux-386.tar.gz
wget https://dist.ipfs.io/go-ipfs/v${version}/go-ipfs_v${version}_linux-amd64.tar.gz

tar -xvf go-ipfs_v${version}_linux-amd64.tar.gz
cd go-ipfs
sudo bash install.sh
cd ..
rm -f go-ipfs_${version}_linux-386.tar.gz
rm -rf go-ipfs/
echo "==> $(ipfs version)"

killall ipfs &>/dev/null

: '
# https://github.com/ipfs/ipfs-cluster
# https://cluster.ipfs.io/download/

cd /tmp
git clone https://github.com/ipfs/ipfs-cluster.git
cd ipfs-cluster
# export GO111MODULE=on # optional, if checking out the repository in $GOPATH.
go install ./cmd/ipfs-cluster-service
go install ./cmd/ipfs-cluster-ctl
go install ./cmd/ipfs-cluster-follow
'
