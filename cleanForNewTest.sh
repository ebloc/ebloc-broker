#!/bin/bash

sudo rm -rf ~/.eBlocBroker/*/*
sudo rm -f ~/.eBlocBroker/my-app.pid
sudo rm -f ~/.eBlocBroker/checkSinfoOut.txt
sudo rm -f ~/.eBlocBroker/logJobs.txt
sudo rm -f ~/.eBlocBroker/queuedJobs.txt
sudo cat /dev/null > nohup.out

# sudo bash killall.sh
