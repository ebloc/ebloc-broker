#!/bin/bash
# To Run:  sudo bash runSlurm.sh
#------------------------------


sudo killall slurmctld slurmdbd slurmd
sudo munged -f
sudo /etc/init.d/munge start 
sudo slurmd
slurmdbd &
# sudo -u $(logname) mkdir -p /tmp/slurmstate
# sudo chown -R $(logname) /tmp/slurmstate
slurmctld -c #-cDvvvvvv
sinfo


# echo "This script must be run as root. Please run:  sudo bash runSlurm.sh" 



