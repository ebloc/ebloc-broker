#!/bin/bash
#                                      |
# To Run:  sudo bash cleanForNewTest.sh|
#---------------------------------------

if [ "$EUID" -eq 0 ]
  then echo "Please run without sudo keyword."
  exit
fi

sudo rm -rf /var/eBlocBroker/*
sudo rm -rf $HOME/.eBlocBroker/*/*
sudo rm -f  $HOME/.eBlocBroker/my-app.pid
sudo rm -f  $HOME/.eBlocBroker/checkSinfoOut.txt
sudo rm -f  $HOME/.eBlocBroker/logJobs.txt
sudo rm -f  $HOME/.eBlocBroker/queuedJobs.txt
sudo rm -f  $HOME/.eBlocBroker/test.txt
sudo rm -f  $HOME/.eBlocBroker/ipfs.out

cat /dev/null > $HOME/.eBlocBroker/clusterDriver.out

sudo bash killall.sh
sudo bash clean.sh

python3 -uB contractCalls/blockNumber.py > $HOME/.eBlocBroker/blockReadFrom.txt
