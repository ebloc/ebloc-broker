#!/bin/bash
slurmd
munged -f
/etc/init.d/munge start #Do to Amazon AWS, you may need to create new user with a password.
slurmdbd
if [ ! -d /tmp/slurmstate ]; then    
    mkdir /tmp/slurmstate 
fi
slurmctld -cv

#sinfo
