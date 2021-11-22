#!/bin/bash

# Set Universal Time (UTC) in Ubuntu
# Required for sync with Bloxberg blockchain
sudo apt install systemd-timesyncd
sudo timedatectl set-timezone UTC
sudo systemctl restart systemd-timesyncd.service
systemctl status systemd-timesyncd
timedatectl status

# pip
~/venv/bin/python3 -m pip install --upgrade pip

# apt_packages
grep -vE '^#' package.list | xargs -n1 sudo apt install -yf package.list

mkdir -p /tmp/run
sudo groupadd eblocbroker

# yaml check in brownie network config file
~/ebloc-broker/broker/python_scripts/add_bloxberg_into_network-config.py
