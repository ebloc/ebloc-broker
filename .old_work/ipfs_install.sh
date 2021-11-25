#!/bin/bash

install_ipfs () {
    ipfs_current_version=""
    which ipfs &>/dev/null
    if [ $? -eq 0 ]; then
        killall ipfs &>/dev/null
        ipfs_current_version=$(ipfs version | awk '{ print $3 }')
        echo ipfs_current_version=v$ipfs_current_version
    fi
    cd /tmp
    version=$(curl -L -s https://github.com/ipfs/go-ipfs/releases/latest | grep -oP 'Release v\K.*?(?= )' | head -n1)
    echo "version_to_download=v"$version
    if [[ "$ipfs_current_version" == "$version" ]]; then
        echo "## Latest version is already downloaded"
    else
        arch=$(dpkg --print-architecture)
        wget "https://dist.ipfs.io/go-ipfs/v"$version"/go-ipfs_v"$version"_linux-"$arch".tar.gz"
        tar -xvf "go-ipfs_v"$version"_linux-"$arch".tar.gz"
        cd go-ipfs
        make install
        sudo ./install.sh
        cd /tmp
        rm -f "go-ipfs_v"$version"_linux-"$arch".tar.gz"
        rm -rf go-ipfs/
        ipfs version
    fi
}  # alternative: sudo snap install ipfs

# Install IPFS: Download the Linux binary from dist.ipfs.io (opens new window).

# Install given version of IPFS. Check latest version from here: https://github.com/ipfs/go-ipfs/releases
# https://gist.github.com/MiguelBel/b3b5f711aa8d9362afa5f16e4e972461

# For macOS: `brew upgrade ipfs`

# pre-requirements
# sudo apt-get install golang-go -y

# https://github.com/ipfs/ipfs-cluster
# https://cluster.ipfs.io/download/

# cd /tmp
# git clone https://github.com/ipfs/ipfs-cluster.git
# cd ipfs-cluster
# # export GO111MODULE=on # optional, if checking out the repository in $GOPATH.
# go install ./cmd/ipfs-cluster-service
# go install ./cmd/ipfs-cluster-ctl
# go install ./cmd/ipfs-cluster-follow
