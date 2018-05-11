#!/bin/bash
#                                      |
# To Run:  sudo bash cleanForNewTest.sh|
#---------------------------------------

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

rm -rf $HOME/.eBlocBroker/*/*
rm -f  $HOME/.eBlocBroker/my-app.pid
rm -f  $HOME/.eBlocBroker/checkSinfoOut.txt
rm -f  $HOME/.eBlocBroker/logJobs.txt
rm -f  $HOME/.eBlocBroker/queuedJobs.txt
rm -f  $HOME/.eBlocBroker/test.txt
rm -f  $HOME/.eBlocBroker/ipfs.out

cat /dev/null > $HOME/.eBlocBroker/clusterDriver.out

sudo bash killall.sh
sudo bash clean.sh

python3 -uB contractCalls/blockNumber.py > $HOME/.eBlocBroker/blockReadFrom.txt
