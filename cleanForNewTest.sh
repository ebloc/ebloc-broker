#!/bin/bash

rm -rf $HOME/.eBlocBroker/*/*
rm -f  $HOME/.eBlocBroker/my-app.pid
rm -f  $HOME/.eBlocBroker/checkSinfoOut.txt
rm -f  $HOME/.eBlocBroker/logJobs.txt
rm -f  $HOME/.eBlocBroker/queuedJobs.txt
rm -f  $HOME/.eBlocBroker/test.txt

cat /dev/null > clusterDriver.out

sudo bash killall.sh
sudo bash clean.sh

python contractCalls/blockNumber.py > $HOME/.eBlocBroker/blockReadFrom.txt
