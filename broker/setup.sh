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
