#!/bin/bash

sudo killall slurmd
sudo munged -f
sudo /etc/init.d/munge start
sudo slurmd -Dvvvvv

# sudo slurmd
# sudo slurmdbd &
# sudo -u $(logname) mkdir -p /tmp/slurmstate
# sudo chown -R $(logname) /tmp/slurmstate
