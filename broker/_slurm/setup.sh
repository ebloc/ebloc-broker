#!/bin/bash

sudo apt-get update
grep -vE '^#' package.list | xargs -n1 sudo apt install -yf
sudo apt autoremove -y

# apt-cache search mysql | grep "dev"
# sudo apt-get install libmysqld-dev
# sudo apt-get install libmysqlclient
