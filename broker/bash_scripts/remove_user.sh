#!/bin/bash

account=$1
sudo userdel $account
sacctmgr remove user where user=$account --immediate
sudo rm -rf /var/ebloc-broker/$1
echo "[  OK  ]"
