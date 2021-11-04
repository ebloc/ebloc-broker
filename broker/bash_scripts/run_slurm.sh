#!/bin/bash

alias sudo='nocorrect sudo'
echo "==> logname="$(logname)
_LOGNAME=$(whoami)
if [[ $(whoami) == "root" ]] ; then
    _LOGNAME="alper"
fi

sudo killall slurmd slurmdbd slurmctld > /dev/null 2>&1
sudo rm -f /var/run/slurmdbd.pid
sudo chown $_LOGNAME -R /var/log/slurm/
DIR="$( cd "$( dirname "$0" )" && pwd )"
sudo $DIR/run_munge.sh
sudo /usr/local/sbin/slurmd # -N $(hostname -s)
sudo /usr/local/sbin/slurmdbd &
sleep 2.0
sudo -u $_LOGNAME mkdir -p /tmp/slurmstate
sudo chown -R $_LOGNAME /tmp/slurmstate
# sudo -u $_LOGNAME /usr/local/sbin/slurmctld -c # -cDvvvvvv
# sudo -u $(logname) /usr/local/sbin/slurmctld -cDvvvvvv
sudo /usr/local/sbin/slurmctld -cDvvvvvv
# sleep 1.0
# squeue | tail -n+2 | awk '{print $1}' | xargs scancel 2> /dev/null
# /usr/local/bin/sinfo -N -l
# scontrol show node
