#!/bin/bash                     |
#                               |
# To Run:  sudo bash runSlurm.sh|
#--------------------------------

if [ "$EUID" -ne 0 ]
  then echo "Please run as root."
  exit
fi

sudo killall slurmctld slurmdbd slurmd
sudo munged -f
sudo /etc/init.d/munge start 
sudo slurmd
slurmdbd &
sudo -u $(logname) mkdir -p /tmp/slurmstate
sudo chown -R $(logname) /tmp/slurmstate
sleep 1
sudo slurmctld -c # sudo slurmctld -cDvvvvvv
sinfo
