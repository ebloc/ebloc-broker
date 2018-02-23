#!/bin/bash

slurmd
sudo munged -f
/etc/init.d/munge start # note: On Amazon AWS, you may need to create new user with a password.
slurmdbd
if [ ! -d /tmp/slurmstate ]; then    
    mkdir /tmp/slurmstate 
fi
slurmctld -c
sinfo
