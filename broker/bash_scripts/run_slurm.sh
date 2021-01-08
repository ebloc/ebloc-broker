#!/bin/bash

# if [ "$EUID" -ne 0 ]
#   then echo "Please run as root"
#   exit
# fi
sudo killall slurmctld slurmdbd slurmd > /dev/null 2>&1

DIR="$( cd "$( dirname "$0" )" && pwd )"
sudo $DIR/run_munge.sh

sudo /usr/local/sbin/slurmd
sudo /usr/local/sbin/slurmdbd &
sleep 1.0
sudo -u $(logname) mkdir -p /tmp/slurmstate
sudo chown -R $(logname) /tmp/slurmstate
sudo -u $(logname) /usr/local/sbin/slurmctld # -cDvvvvvv
sleep 1.0
/usr/local/bin/sinfo
