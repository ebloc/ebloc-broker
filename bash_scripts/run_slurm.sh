#!/bin/bash

# if [ "$EUID" -ne 0 ]
#   then echo "Please run as root"
#   exit
# fi
sudo echo ""
sudo killall slurmctld slurmdbd slurmd > /dev/null 2>&1

sudo munged -f
sudo /etc/init.d/munge start
sudo slurmd
sudo slurmdbd &
sleep 1
sudo -u $(logname) mkdir -p /tmp/slurmstate
sudo chown -R $(logname) /tmp/slurmstate
sudo slurmctld -c

# sudo slurmctld -cDvvvvvv
/usr/local/bin/sinfo
