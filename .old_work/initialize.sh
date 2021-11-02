#!/bin/bash

setup=0
MACHINE_OS=$(bash $HOME/ebloc-broker/broker/bash_scripts/machine.sh)
if [ "$MACHINE_OS" == "Mac" ]; then
    brew install coreutils
    CFLAGS="-Wno-error=implicit-function-declaration" pip install reportlab
    CFLAGS="-Wno-error=implicit-function-declaration" pip install -e .
    return
else
    grep -vE '^#' package.list | xargs -n1 sudo apt install -yf package.list
fi

mkdir -p /tmp/run
sudo groupadd eblocbroker
