#!/bin/bash

# What are correct permissions for /tmp ? I unintentionally set it
# all public recursively. https://unix.stackexchange.com/a/71625/198423
sudo chmod 1777 /tmp
sudo find /tmp -mindepth 1 -name '.*-unix' -exec chmod 1777 {} + -prune -o -exec chmod go-rwx {} +

## gdfuse
# https://github.com/astrada/google-drive-ocamlfuse/wiki/Headless-Usage-&-Authorization

# shared_with_me=true to have read-only access to all your "Shared with me" files under ./.shared.
sed -i.bak "s/^\(download_docs=\).*/\1false/" $HOME/.gdfuse/me/config
sed -i.bak "s/^\(shared_with_me=\).*/\1true/" $HOME/.gdfuse/me/config
# https://github.com/astrada/google-drive-ocamlfuse/issues/499#issuecomment-430269233
# download_docs=false

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
