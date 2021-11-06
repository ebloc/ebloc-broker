#!/bin/bash

# What are correct permissions for /tmp ? I unintentionally set it
# all public recursively. https://unix.stackexchange.com/a/71625/198423
sudo chmod 1777 /tmp
sudo find /tmp -mindepth 1 -name '.*-unix' -exec chmod 1777 {} + -prune -o -exec chmod go-rwx {} +

## Install python3.7
sudo apt-get update
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.7
sudo apt install python3.7-dev
sudo apt install python3
sudo apt install python3-venv
sudo apt install unixodbc-dev
sudo apt install python-dev

VENV_PATH=$HOME/venv
python3 -m venv $VENV_PATH
source $VENV_PATH/bin/activate
~/venv/bin/python3 -m pip install --upgrade pip
pip install -e . --use-deprecated=legacy-resolver

## npm
wget -qO- https://deb.nodesource.com/setup_7.x | sudo bash -
sudo npm install -g n # npm install --save
sudo n latest
sudo npm install -g --unsafe-perm=true --allow-root ganache-cli  # npm install -g ganache-cli
# npm install dotenv

# mongodb guide => https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/
# sudo mkdir /var/lib/mongodb
# sudo mkdir /var/log/mongodb
# sudo mkdir -p /data/db
#
# sudo chown -R mongodb:mongodb /var/lib/mongodb
# sudo chown mongodb:mongodb /tmp/mongodb-27017.sock
#
# sudo service mongod start
# service mongod status | systemctl status mongodb
# ----------------------------------------------------------

## gdfuse
# https://github.com/astrada/google-drive-ocamlfuse/wiki/Headless-Usage-&-Authorization

# shared_with_me=true to have read-only access to all your "Shared with me" files under ./.shared.
sed -i.bak "s/^\(download_docs=\).*/\1false/" $HOME/.gdfuse/me/config
# https://github.com/astrada/google-drive-ocamlfuse/issues/499#issuecomment-430269233
# download_docs=false
sed -i.bak "s/^\(shared_with_me=\).*/\1true/" $HOME/.gdfuse/me/config

sudo apt-get install mailutils -y

# Clone the source repository
cd ~/
git clone https://github.com/ipfs/py-ipfs-http-client.git
cd py-ipfs-http-client
flit install --pth-file  # Link ipfs-api-client into your Python Path

# - name: bloxberg (Bloxberg)
#   id: bloxberg
#   chainid: 8995
#   host: https://core.bloxberg.org
#   explorer: https://blockexplorer.bloxberg.org/api
