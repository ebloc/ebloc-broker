#!/bin/bash

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
