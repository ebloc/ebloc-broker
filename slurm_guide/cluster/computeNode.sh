#!/bin/bash
#                                   |
# To Run:  sudo bash computeNode.sh |
#-----------------------------------

if [ "$EUID" -ne 0 ]
  then echo "Please run as root."
  exit
fi

sudo killall slurmd
sudo munged -f
sudo /etc/init.d/munge start 
sudo slurmd -Dvvvvv
# sudo slurmd


#sudo slurmdbd &
#sudo -u $(logname) mkdir -p /tmp/slurmstate
#sudo chown -R $(logname) /tmp/slurmstate


