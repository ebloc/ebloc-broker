#!/bin/bash

alias sudo='nocorrect sudo'
USER=$(whoami)
if [[ $(whoami) == "root" ]] ; then
    echo "==> logname="$(logname)
    USER=$(logname)
fi

verbose=false
sudo killall slurmd slurmdbd slurmctld > /dev/null 2>&1
sudo rm -f /var/run/slurmdbd.pid
sudo chown $USER /var/run/slurmctld.pid 2>/dev/null
sudo chown $USER -R /var/log/slurm/
DIR="$( cd "$( dirname "$0" )" && pwd )"
sudo $DIR/run_munge.sh
sudo /usr/local/sbin/slurmd
# sudo /usr/local/sbin/slurmd -N $(hostname -s)  # emulate mode
sudo /usr/local/sbin/slurmdbd &
sleep 2.0
sudo -u $USER mkdir -p /tmp/slurmstate
sudo chown -R $USER /tmp/slurmstate
if [ "$verbose" = true ] ; then
    sudo /usr/local/sbin/slurmctld -cDvvvvvv  # verbose
    # sudo -u $(logname) /usr/local/sbin/slurmctld -cDvvvvvv
else
    sudo -u $USER /usr/local/sbin/slurmctld -c
    sleep 1.0
    squeue | tail -n+2 | awk '{print $1}' | xargs scancel 2> /dev/null
    /usr/local/bin/sinfo -N -l
    echo ""
    scontrol show node
fi
