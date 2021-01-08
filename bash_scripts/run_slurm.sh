#!/bin/bash

# if [ "$EUID" -ne 0 ]
#   then echo "Please run as root"
#   exit
# fi
sudo killall slurmctld slurmdbd slurmd > /dev/null 2>&1

DIR="$( cd "$( dirname "$0" )" && pwd )"
sudo $DIR/run_munge.sh

sudo slurmd
sudo slurmdbd &
sleep 1
sudo -u $(logname) mkdir -p /tmp/slurmstate
sudo chown -R $(logname) /tmp/slurmstate
sudo slurmctld -c

# sudo slurmctld -cDvvvvvv
/usr/local/bin/sinfo
