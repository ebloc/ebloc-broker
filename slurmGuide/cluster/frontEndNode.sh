#!/bin/bash
# Run before computeNode.sh      |
# To Run:  sudo bash frontEndNode|
#---------------------------------

if [ "$EUID" -ne 0 ]
  then echo "Please run as root."
  exit
fi

sudo killall slurmctld slurmdbd slurmd
sudo munged -f
sudo /etc/init.d/munge start 

sudo slurmdbd &
sudo -u $(logname) mkdir -p /tmp/slurmstate
sudo chown -R $(logname) /tmp/slurmstate
sudo slurmctld -cDvvvvvv


# sudo slurmctld -c
# sinfo
# sudo slurmd # No need to run.
