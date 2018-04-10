#!/bin/bash

sudo rm -rf $HOME/.eBlocBroker/*/*
sudo rm -f  $HOME/.eBlocBroker/my-app.pid
sudo rm -f  $HOME/.eBlocBroker/checkSinfoOut.txt
sudo rm -f  $HOME/.eBlocBroker/logJobs.txt
sudo rm -f  $HOME/.eBlocBroker/queuedJobs.txt
sudo rm -f  $HOME/.eBlocBroker/test.txt

sudo cat /dev/null > clusterDriver.out

sudo bash killall.sh
sudo bash clean.sh

python contractCalls/blockNumber.py > $HOME/.eBlocBroker/blockReadFrom.txt
