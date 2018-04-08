#!/bin/bash
# To Run: sudo bash runSlurm.sh
#------------------------------

sudo killall slurmctld slurmdbd slurmd

sudo slurmd
sudo munged -f
sudo /etc/init.d/munge start 
slurmdbd &
mkdir -p /tmp/slurmstate 

slurmctld -c
#slurmctld -cDvvvvvv
sinfo
