#!/bin/bash
# To Run: sudo bash runSlurm.sh
#------------------------------

sudo killall slurmctld slurmdbd slurmd

sudo slurmd
sudo munged -f
sudo /etc/init.d/munge start 
slurmdbd &

if [ ! -d /tmp/slurmstate ]; then    
    mkdir /tmp/slurmstate 
fi

slurmctld -c
#slurmctld -cDvvvvvv

sinfo
